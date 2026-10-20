# Consultation → booking → completion: verification and minimal proposal

2026-10-18, Asia/Manila. **Inspection DONE / source and configured database metadata VERIFIED. Design PROPOSED. Implementation NOT STARTED.** Inspected checkout `I:/HAIR`, branch `codex/look-details-performance`, source commit `984ed46`. No application code, migration, database row, model, runtime flag, Render configuration or deployment was changed. This proposal targets BeautyCore web; native parity is not asserted.

The architecture already supports much of the journey. The missing parts are a single selected-look booking handoff, home-dashboard presentation, stronger completion semantics, verified reviews/ratings, rankings and structured actual product usage. Profit is a separate accounting requirement and is not supported by the current financial data.

## 1. Verification boundary and database findings

A read-only Neon transaction inspected public table/column/constraint/function metadata only. It did not retrieve account/client/appointment/image records, export rows or apply schema changes. The configured database has six tables: `users`, `client_profiles`, `appointments`, `ai_generations`, `inventory`, `ai_runtime_endpoints`.

- `appointments.ai_generation_id` and the same-client `appointments_look_owner_fk` exist.
- Saved-image metadata and the original `beautycore_save_look` function exist.
- **`ai_generations.look_details` and `beautycore_save_look_with_details` are absent.** Their additive migration `0004_look_details.sql` exists locally and is not applied to this configured database.
- No completion timestamp, reviews/ratings, appointment-product usage, payment or expense tables were found.
- Inventory has integer `current_stock`, `minimum_threshold`, nullable integer `unit_price` and status/restock metadata. It has no structured brand, measurement unit, consumption link or movement history.

This verifies the local configured Neon schema, not independently that Render currently points at the same database branch or runs this checkout. Actual Render revision/feature flag activation and live client/stylist screens remain **Needs verification**. Do not call local implementation a deployed feature.

**Release dependency:** current local appointment-list SQL selects `g.look_details` even when saved-look creation is disabled. Deploying this checkout before0004 can break ordinary appointment listing, not just new saves. Migrate/test before a separately authorized release; nothing was migrated in this audit.

## 2. Workflow status

| Requested step | Verified implementation | Gap / scope decision |
| --- | --- | --- |
| Client consultation/preferences | Web photo/service/preferences/chat flow and backend session/provider validation exist. | Temporary session, not a persistent appointment record. Do not infer that full chat/preferences carry to booking. |
| Three looks with images | Three recommendations are generated sequentially, with pending/completed/failed/unknown recovery. | Three alternatives for the selected primary feature. Complement suggestions are text-only, not additional Hair+Makeup+Nails images or combined packages. |
| Description/estimated cost | Local web uses shared `LookInformation` and actual service-catalog options; new saved metadata captures description/estimates/version/time. | New metadata migration is pending. Makeup and unmapped services may require a quote; no universal fixed style price. Backend/native demo numeric estimate contract is not authoritative booking pricing. |
| Choose a look | Completed recommendation can be selected in the consultation store/UI. | Select stores a session recommendation ID. Save/Book is a separate action on the currently displayed completed card; selection is not a prerequisite and may differ. No automatic persistent save/booking occurs on Select. |
| Book image + stylist | Book This Look saves once then routes to `/booking?look=<saved-id>`. Booking validates owner, feature/category, catalog service, future timestamp and stylist role; server derives the amount. | Stylist remains optional (“No preference”). No real availability, overlap, shift, duration or specialty enforcement. Retain existing rules unless the client explicitly requires more. |
| Both home dashboards | Both fetch appointment data with the joined look available from the API. | Neither home dashboard renders the shared requested-look preview. Detailed Client/Stylist Appointments pages already show it, with description/estimate in the dialog. |
| Revisit booked look | Durable generation reference, account gallery and role-protected image endpoint exist. Hiding a gallery look does not remove its appointment reference. | Unsaved consultation images/session disappear on expiry/restart. Persist the chosen result before navigation; no need to persist all three. |
| Stylist completes service | Assigned stylist has a Complete button and PATCH status action. Client status appears after fetching appointments again. | Generic status dropdown/API allow reversal/re-completion; no completed_at/by or idempotent completion product record. Home screens fetch on mount, not realtime; client home mostly shows upcoming bookings. |
| Review/rating | No table, API or submission/display/rating aggregation found. | New small feature, bound to a completed owned appointment and its assigned stylist. |
| Admin completed counts | Daily Services by Stylist already groups statuses/counts and sums completed recorded amounts by scheduled Manila service day. | Ranking/ratings absent. Keep current report basis rather than silently redefining it as actual completion day. |
| Salon financial performance/profit | Completed-service recorded totals/monthly totals/service breakdown and unpriced counts exist. | No payment collection, material consumption cost, commission, rent/payroll/utilities or expense ledger. Existing totals are not actual receipts or net profit. |
| Products/inventory | Admin CRUD and manual stock adjustment plus low-stock alerts exist; stylists may read inventory. | No brand field, per-service usage, automatic deduction, unit conversion, cost history or purchasing ledger. |

## 3. Source evidence

Paths and line numbers below refer to the inspected source commit (no code was edited in this audit).

| Area | Evidence |
| --- | --- |
| Three sequential looks, selection, separate per-card Save/Book and selected summary | `beautycore/app/client/ai-consultation/page.tsx:154`, `:272`, `:425`, `:428`, `:453` |
| Temporary session and completed-only selection | `backend/app/consultation/store.py:14`, `:200`, `:242`; `backend/app/consultation/api.py` |
| Actual-catalog descriptions/conditional estimates | `beautycore/lib/business/look-information.ts:46`; `beautycore/lib/services.ts`; `beautycore/components/look-information.tsx` |
| Save-before-book | `beautycore/components/saved-look-actions.tsx:25`; `beautycore/lib/business/core.ts:97` |
| Booking form, look loading and optional stylist | `beautycore/app/(public)/booking/booking-form.tsx:43`, `:83`, `:305`; `beautycore/app/api/stylists/route.ts` |
| Catalog/owner/look/date/role checks; status mutation scope | `beautycore/lib/business/api.ts:191`, `:216`, `:255`, `:264`; route wrappers in `app/api/appointments/` |
| One image joined into appointments and private access | `beautycore/lib/business/store.ts:37`, `:103`, `:110`; `beautycore/db/schema.ts:63`, `:106` |
| Existing detail previews | `beautycore/components/appointment-look.tsx:14`; client/stylist `app/*/appointments/page.tsx:177` / `:169` |
| Home cards lack look component | `beautycore/app/client/dashboard/page.tsx:175`; `beautycore/app/stylist/dashboard/page.tsx:165` |
| Completion button plus unrestricted dropdown | `beautycore/app/stylist/appointments/page.tsx:178`; `beautycore/lib/business/api.ts:264` |
| Existing daily figures and basis | `beautycore/lib/business/store.ts:160`; `beautycore/lib/business/api.ts:289`; `beautycore/components/daily-services.tsx:78` |
| Recorded totals versus receipts | `beautycore/app/api/admin/stats/route.ts`; `beautycore/app/admin/finance/page.tsx:95` |
| Inventory fields/CRUD | `beautycore/db/schema.ts:93`; `beautycore/app/api/inventory/route.ts`; `beautycore/app/admin/inventory/page.tsx` |
| Pending snapshot dependency and current flag | `beautycore/db/migrations/0004_look_details.sql`; `beautycore/lib/business/server.ts`; `beautycore/lib/business/store.ts:49` |

## 4. Minimum data flow

`Temporary consultation → completed selected result → existing saved ai_generations row → appointments.ai_generation_id → shared client/stylist previews → controlled completion + actual product lines → one verified review → admin aggregates`

1. Choose a completed recommendation, then use one consistent **Book selected look** action. It should select that same recommendation and reuse the existing save/booking action. No new AI generation is required. Do not require every alternative to succeed unless that is a confirmed business rule.
2. Store the chosen generated image once, with the existing server-owned immutable style/description/estimate snapshot. Pass its saved ID to booking; retain the current owner/category/FK checks. The database currently receives browser-submitted validated result bytes, not a verified persistent consultation-ID/rec-ID relationship. Simple consistent UI handoff is sufficient unless stronger AI-result provenance is explicitly required.
3. Keep selected service, actual appointment amount, preferred/assigned stylist and booking notes on the existing appointment. The saved estimate is a reference, not a bill; starting-from and unknown prices must stay labeled. No duplicate image, stylist or client record is needed.
4. Reuse the existing joined appointment response and `AppointmentLookPreview` on both dashboard home cards. Keep full history in Appointments. Add a small recent-completed section for client status/review access and refresh-on-focus/manual refresh; do not add WebSockets merely to reflect completion.
5. On completion, persist a server timestamp/actor and actual product lines atomically. Then permit the owner to create one review of the assigned stylist. Aggregate from these records; do not store cached rank/count columns on users.
6. Keep AI-generated descriptions and actual staff service records separate. Do not append stock usage/brands/costs into immutable `look_details` or mutate the AI photo.

Current booking notes are separate from consultation preferences/chat. If the client wants preferences carried forward, approve an editable concise summary into existing notes; do not silently copy the whole conversation or create another chat-history subsystem.

## 5. Proposed essential changes after review

### A. Finish existing handoff and displays

- Make Select and Book operate on the same completed card; add/reuse a selected-summary booking action so users cannot unknowingly book a different visible card.
- Add look preview/description/estimate to Client and Stylist Dashboard home cards using the existing shared component, plus a route to the full appointment.
- Preserve actual booking amount separately; show chosen stylist or Unassigned explicitly. Continue existing optional stylist choice/admin assignment until mandatory selection is confirmed.
- Keep completed records accessible and refresh status on navigation/focus. Remove completed bookings from Upcoming presentation when adding a completed section; current filters exclude cancelled, but can still include completed future bookings.

### B. Make completion a reliable event

- Add nullable `completed_at` (timezone-aware) and `completed_by` on appointments for newly completed services; do not fabricate timestamps for historical completed rows.
- Keep an explicit **Mark as Completed** action/form. Preserve the current ability to complete pending or confirmed assigned appointments unless the salon approves a confirmed-first rule.
- Make completed/cancelled states terminal for ordinary stylist edits. A repeated completion must return the existing result rather than insert product lines twice. Handle conflicting concurrent requests safely.
- Reuse current business API/store/Origin/role checks; complete, record product lines and timestamp in one database transaction/function, consistent with the existing atomic-save pattern. No new backend service is necessary.
- Protect completed stylist attribution, booked-look link and financial history against casual dropdown edits, reassignment or hard deletion. Admin corrections require an explicit, reviewed rule rather than silently reopening completed appointments.
- Current null/from amounts may not be salon-confirmed final charges. Preserve unpriced reporting and existing admin amount control. Whether a final amount is mandatory before completion is a business decision still to confirm.

### C. Add verified reviews and simple rankings

- One proposed `appointment_reviews` table: unique appointment FK, server-derived client and stylist attribution, integer1–5 rating, bounded optional comment and created timestamp. Do not trust client-supplied stylist/client IDs.
- Owner-only submission after completion, with a known assigned stylist; reject pending/cancelled/foreign appointments. Keep exactly one record under retries/concurrency. Proposed first version is one submission, no public review site or moderation workflow.
- Show the submitted review in the client's completed appointment and an admin/stylist view appropriate to their role. Do not invent scores for unrated stylists.
- Reuse daily reporting and add a small per-stylist aggregate: completed count, average verified rating and review count. Propose two clearly labeled sorts: completed-service count and average rating. Do not introduce an opaque weighted combined score. Tie/minimum-sample rules need approval before a single formal “best stylist” rank is claimed.
- Keep appointment-count semantics: one appointment currently records one service. Do not claim a count of multiple service line items that the data model does not contain.

### D. Record actual products during completion

This belongs to **service completion**, because the stylist knows what was actually used. A consultation may record a client's requested/avoided brand as a preference, but it cannot establish actual consumption.

Recommended minimum for future statistics:

- Reuse existing `inventory` as the optional product source; add a simple optional `brand` field there if consistent catalog brands are desired. Do not create a second product master or a service-recipe engine.
- One proposed `appointment_product_usage` child table: appointment FK; optional existing inventory FK; product-name and brand snapshots; optional positive quantity plus explicit unit; optional salon-confirmed cost per that same unit; recorder/time. Allow an unlisted product/brand entry without forcing fake stock creation. Keep omitted quantity/cost as unknown, not zero.
- Snapshot name/brand/unit/cost so renaming/repricing/deleting an inventory item cannot rewrite historical usage. An optional inventory reference can become null on catalog deletion while historical snapshots remain. Guard completed appointment deletion to retain service history.
- Quantity requires a unit; costs require a defined basis and currency/precision. Existing `unit_price` is displayed as “each” and is not established as purchase cost or cost perml/g. Do not silently repurpose it. If costs are omitted, track coverage and do not present incomplete margins as full profit.
- Initially **record usage without automatic stock deduction**. Existing stock is integer package counts: “1 bottle” and “20ml” are not interchangeable. Group usage statistics by compatible product/unit. Admin manual stock adjustment continues.
- If automatic deduction is later requested, first confirm base units/package conversion, fractional quantities, stock-opening values, adjustment/reversal rules and concurrency. That is a separate stock-movement increment, not a prerequisite for brand recording.

For a strictly brands-only release, omit quantity/cost fields from the visible form while retaining structured product lines. Putting names in a free-text notes field is smaller but does not reliably support future per-brand/quantity statistics; it is not the recommended data path.

## 6. Financial scope and honest labels

Essential existing-compatible reports: completed-service counts, recorded completed-service amounts, unpriced counts, average verified ratings and review counts, optional recorded usage totals/cost coverage.

**Net salon profit is not available from current records.** Service amount minus recorded materials would be, at best, a partial service margin; payroll, stylist commission, rent/utilities/other expenses and payment/refund timing are absent. Do not deduct current inventory stock value and call it expenses or profit. Earlier Supervisor guidance selected completed-service amounts rather than a payment ledger; the new word “profit” needs clarification before broadening that decision.

Retain the current scheduled Asia/Manila service-day basis for existing daily reports and initial stylist rankings. A completion timestamp improves auditability but does not justify silently changing old reports to completion-day totals. Confirm a separate completion-day view if needed; historical completion time remains unknown.

## 7. Risks and dependencies

- **Migration order:**0004 is pending on the configured database; a future additive review/usage/completion migration follows it. Do not deploy code requiring absent fields/functions. A feature flag does not protect the current unconditional appointment look join.
- **Lost result:** consultation state/photos/results are process-local with a sliding one-hour lifetime; selection alone is not durable. Save before leaving and preserve booked references when a gallery item is hidden.
- **Two selections:** selected consultation recommendation and current displayed card can differ today. Tie the Book action to one ID; do not rebuild consultation storage unnecessarily.
- **Money:** estimate versus catalog starting amount versus confirmed final service amount versus actual payment/profit are separate concepts. Missing prices stay unknown. Existing whole-peso fields do not define future fractional material-cost precision.
- **Concurrency/history:** status reversal/repeated completion must not duplicate product records or reviews. Preserve attribution under reassignment and consider existing hard-delete APIs before adding FKs.
- **Report duplication:** product usage is one-to-many; aggregate usage/reviews separately before joining to appointment totals, or revenue/counts can multiply. Use existing role-scoped batches/joins and FK indexes rather than one query per appointment.
- **Availability:** no enforced schedule-conflict/shift/specialty logic exists. Do not promise an availability engine as an existing rule.
- **Refresh/dates:** dashboard state loads on mount and today filters use browser-local date comparisons; use existing Manila date helpers where touching those views. A focus/manual refresh is enough for the initial status requirement.
- **Architecture scope:** no retraining, prompt changes, extra AI calls, new cloud service, payment gateway, purchasing system, cost-accounting engine, realtime infrastructure or native rebuild is required for this essential web workflow. The separate Nails cache work is not a dependency.

## 8. Acceptance plan after implementation approval

| Area | Minimum verification |
| --- | --- |
| Selected look | Generate three fixture options; select B while viewing A; Book selected must persist/link B and preserve its snapshot without another generation. Reject failed/placeholder selections. |
| Persistence/access | Reload gallery and both home/detail views; same image/snapshot/assigned stylist; wrong client/unassigned stylist denied; hiding gallery item leaves booked reference. |
| Booking | Existing catalog/category/date/stylist/Origin checks preserved; null/from estimates labeled; actual amount derived server-side; no invented availability guarantee. |
| Completion | Assigned stylist/admin only; one completed timestamp/actor; allowed transition matrix; double-click/concurrent retry idempotent; atomic rollback if product validation fails. |
| Products | Existing/unlisted product, brand snapshot, unknown values, positive quantities with units, cost basis; no unintended stock deduction; rename/delete catalog item does not rewrite history. |
| Reviews | Owner of completed assigned appointment only;1–5 range, bounded comment, unique submission under concurrent retry; others denied; unrated mean stays null. |
| Reports | Completed/pending/cancelled/unpriced cases; ratings/sample counts; tie policy; same date range/timezone; multi-product appointment does not multiply count/revenue. |
| Compatibility | Legacy no-look/no-completion-time appointments still render; no invented historical timestamp; shared Finance/Dashboard/history/AI flows remain working. |
| Release | Disposable database migration rehearsals first, explicit migration-before-deploy, then separately approved browser/client/stylist/admin demo. No release in this audit. |

Current audit reran `npm run test:business`: **36passed,0failed**, using disposable PGlite/DOM fixtures. This validates existing behavior, not the unimplemented review/product/ranking features or current live UI. No new tests or source code were written for this planning task.

## 9. Decisions needed before coding

1. Does “profit” mean the existing recorded-service revenue, partial material margin, or actual net profit? Keep net-profit accounting optional until defined.
2. Is preferred stylist still optional, and are three options for one primary feature the intended consultation scope?
3. Is product/brand recording required for every completion or optional/no-product allowed? Should quantity/cost initially be optional, and who confirms cost/final service amounts?
4. For rankings, choose separate completed-count/rating views or confirm one ordering/tie/sample policy. Confirm review editing/admin correction expectations; first version proposes one submission.
5. Keep scheduled Manila service day for existing reports, or request a separate actual-completion-day report? Historical actual completion time cannot be recovered from the present schema.

**Recommended first release:** finish existing selected-look/dashboard handoff, controlled completion with structured actual product lines, one verified review per appointment, and simple transparent admin counts/ratings. Reuse current recorded-service financial reports. Defer stock automation, true profit accounting, advanced scheduling and weighted/public ranking systems.


## Development update — 2026-10-20

Supervisor's “lets start” confirms the minimum local web implementation. Selected-result booking, home/detail previews, atomic completion/product lines, one verified review and transparent admin count/rating sorts are implemented locally. Product/quantity/cost stay optional, preferred stylist remains optional at booking (assignment required before completion), and scheduled Manila service-day reporting remains. Admin amount/notes correction is preserved; reopening/reassignment/deletion and post-completion product/review edits are unavailable. No stock automation/net-profit ledger, GPU change, live database mutation or Render deployment. Original inspection above is dated historical evidence, not a claim about this new local checkout. See [testing/release guide](../guides/consultation-booking-workflow-testing.md) and the development evidence record for acceptance results.
