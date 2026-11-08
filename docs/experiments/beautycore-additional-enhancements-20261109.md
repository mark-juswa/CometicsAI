# BeautyCore additional enhancements — 9 November 2026

Status: DONE for implementation, isolated functional verification, and additive database installation. Browser visual review and real external AI generation remain NEEDS VERIFICATION.

## Implemented behavior

- Sign-in no longer displays demo accounts or sample passwords. Existing accounts and authentication records were preserved.
- Admin client cards open a dedicated account and service-history page. It includes contact details, appointment/service/date/stylist filters, prices, appointment status, payment totals, balances, and individual receipts.
- Actual payments are recorded separately from appointment prices. Existing service amounts are not fabricated into payment receipts. Payment entry validates the balance and uses an idempotency key; reducing a service price below recorded payments is rejected.
- Finance includes a searchable, paginated receipt history, filtered by payment method and Philippine received date. Existing completed-service reports remain available.
- Stylists have a persistent availability switch and editable weekly working hours. The switch saves immediately. Existing appointments remain intact when availability is OFF; notes and amount corrections to those appointments remain possible.
- Selecting an active, qualified stylist automatically confirms a new appointment only when its full service duration fits working hours and does not overlap an active booking. No-preference requests remain pending until assignment. Backend functions and triggers serialize assignment and availability changes using the same database advisory lock.
- New authenticated consultation sessions, accepted uploaded photos, conversation snapshots, and completed generated results are archived at the existing Next.js API boundary. Local synchronous and hosted asynchronous job results are supported. The existing upstream forwarding, model code, prompts, inference parameters, and generation retries were not changed.
- Customers can view their archived sessions and save a completed result after returning to their account. Distinct generated variations retain separate records. Identical image data is deduplicated without overwriting earlier images.
- The consultation image picker distinguishes uploaded references from saved generated looks, previews them, and loads the chosen private bytes into the existing File upload flow. Earlier private data-URL source images already stored in generation records are also reusable without rewriting them.
- Admin and stylist layouts share responsive form/table/card styles. Individual pages received loading/error feedback, account and appointment filters, service search, staff work-status indicators, phone editing, and improved mobile working-hours controls.

## Main files and components

All paths below are relative to `beautycore/`.

| Area | Files |
| --- | --- |
| Sign-in | `app/(public)/login/login-form.tsx` |
| Client detail | `app/admin/clients/page.tsx`, `app/admin/clients/[id]/page.tsx`, `components/client-history.tsx` |
| Payments | `components/payment-history.tsx`, `app/admin/finance/page.tsx`, `app/api/admin/payments/route.ts`, `app/api/admin/clients/[id]/payments/route.ts` |
| Customer history API | `lib/business/customer-history.ts`, `lib/business/history-server.ts`, `app/api/admin/clients/[id]/route.ts`, `app/api/client-images/route.ts`, `app/api/client-images/[id]/route.ts`, `app/api/consultation-history/route.ts`, `app/api/consultation-history/[id]/route.ts` |
| Private archive integration | `app/api/ai/[...path]/route.ts`, `components/consultation.tsx`, `components/reference-image-picker.tsx`, `components/consultation-history.tsx`, both `app/client/consultation-history/` pages, `components/ClientSidebar.tsx` |
| Availability / booking | `lib/business/work-availability.ts`, `app/api/stylist/availability/route.ts`, `components/work-availability.tsx`, `app/api/stylists/route.ts`, `lib/business/api.ts`, `lib/business/store.ts`, `app/(public)/booking/booking-form.tsx` |
| Management UI | `app/globals.css`, `components/ui.tsx`, `components/Sidebar.tsx`, admin/stylist layouts and existing dashboard, appointment, client, stylist, inventory, finance, security, profile, and service-menu pages |
| Database / upgrade | `db/schema.ts`, `db/migrations/0008_work_availability.sql`, `db/migrations/0009_customer_history.sql`, `scripts/saved-look-migrations.ts`, `scripts/apply-saved-looks.ts`, `scripts/business-preservation.ts`, `package.json` |
| Verification | `tests/additional-features.test.ts`, `tests/business-ui.test.mjs`, `tests/business-workflows.test.ts`, `tests/service-completion.test.ts`, `tests/finance-stats.test.mjs`, `tests/saved-look-migrations.test.ts` |

## Database installation and preservation

The pre-upgrade metadata check established that migration 0007 was already installed and the additional availability, history, and receipt structures were absent.

`npm run db:apply:enhancements` applied only 0008 and 0009 to the configured database in one atomic transaction. It briefly locked the existing business tables, computed canonical row fingerprints, installed the additive schema/functions, and compared every existing table's fingerprints before commit. The guard was separately tested with an intentional accidental update; it raised an error and the entire transaction rolled back.

The real upgrade returned `workAvailabilityApplied=true`, `customerHistoryApplied=true`, `paymentsApplied=true`, and `existingRecordsPreserved=true`.

| Existing table | Preserved rows |
| --- | ---: |
| users | 11 |
| appointments | 25 |
| ai_generations | 59 |
| client_profiles | 7 |
| inventory | 18 |
| stylist_specialties | 8 |
| inventory_transactions | 0 |
| appointment_reviews | 0 |
| appointment_product_usage | 0 |

New structures: `stylist_work_settings`, `client_consultations`, `client_reference_images`, `client_consultation_results`, `client_consultation_jobs`, and `appointment_payments`. Foreign keys enforce consultation/image/generation ownership. Uploads reuse the existing database image storage approach and share the saved-look storage budget. No production seed, truncation, account reset, or image rewrite was run.

The upgrade console initially retained an older `schema-only` description despite performing record-fingerprint checks. That report wording has been corrected: metadata-only checks and record-preservation verification are now described separately.

## API changes and privacy

- `GET /api/admin/clients/[id]`: account, appointment, service and receipt metadata only; no consultation/image history.
- `POST /api/admin/clients/[id]/payments`: admin receipt entry, balance validation, same-origin protection and idempotency.
- `GET /api/admin/payments`: admin receipt report and filters.
- `GET/PUT /api/stylist/availability`: authenticated stylist's own settings only; spoofed staff IDs, malformed schedules and foreign origins are rejected.
- `GET /api/stylists`: current account status, specialties, work availability, weekly hours and duration-aware conflicts filter booking options. Admin management retains the full roster and account email.
- `POST/PATCH /api/appointments`: database-enforced assignment and confirmation; existing bookings remain manageable when availability is off. Only the customer can submit their private saved image with a new booking. Administrators and stylists cannot manufacture an appointment attachment to gain access to an unsubmitted image.
- `GET /api/client-images` and `/api/client-images/[id]`: owner-only image library and private uploaded-image bytes.
- `GET /api/consultation-history` and `/api/consultation-history/[id]`: owner-only archived sessions, references, conversation and results.
- `/api/ai/[...path]`: authenticated archive integration surrounds the unchanged forwarding primitive. An admitted generation is never replayed because archiving failed; its preview is retained with an archive warning.

All private archive APIs reject admins and stylists. Image responses use `private, no-store` and `nosniff`. Saved generation access for salon personnel remains limited to an image the customer submitted with a corresponding appointment, scoped to the assigned stylist where applicable. No public storage URLs or unrestricted admin gallery were introduced.

## Verification evidence

- Full business suite: **75 passed, zero failed** before the final booking-provenance guard.
- Final affected backend suites after that guard: **45 passed, zero failed**, including the new direct-API privilege-escalation regression. There are **76 distinct business tests** in the final source.
- Automated UI checks cover immediate availability persistence, retaining confirmed appointments, selecting and previewing saved image bytes without generation, actual payment entry, existing consultation generation/selection, saved-look booking, and role-scoped dashboards.
- Migration tests verify repeated installation, enum transaction boundaries, rollback, preservation of legacy rows, and the accidental-update preservation guard.
- TypeScript check passed; final production build passed, including its TypeScript phase and all new routes. The initial sandboxed font download failed; the normal build passed after network access to the existing Google Fonts was permitted.
- Protected-source comparison: **265 files checked; zero changed hashes** against the local before manifest. Existing unrelated dirty worktree changes were preserved. No model weights, datasets, LoRA adapters, Kaggle resources, protected AI sources, prompts, inference parameters, or generation code were edited or executed.
- The temporary local verification server was stopped. No cloud deployment was performed.

## Limits and operational notes

- Earlier expired in-memory consultation conversations/results cannot be recovered if they were never stored. Existing saved looks and private data-URL reference images are preserved and reusable; new sessions receive durable archives.
- Existing stylists default to not available until they set their actual weekly hours and turn availability ON. No invented working schedules were assigned to real accounts. Hours are same-day weekly intervals in `Asia/Manila`.
- Scheduling uses the existing service catalog's durations. Entries without a stated duration retain the existing 60-minute fallback; actual salon durations should be confirmed.
- Payment receipts start empty because historical appointment prices do not establish that a payment was received.
- Storage remains bounded by `SAVED_LOOKS_STORAGE_BYTES`; storage failures are reported without resubmitting an admitted generation. Guest trials retain their existing temporary behavior.
- Browser visual review remains **NEEDS VERIFICATION**: the in-app browser could not reach the local server, and native browser control was stopped by the tool's safety check because it could not confidently identify the current URL. No browser safety check was bypassed. Real desktop/tablet/mobile visual acceptance was not claimed.
- No live Gemini/Kaggle image-generation request or real cloud concurrency/load test was performed. SQL and UI integration checks used an isolated PostgreSQL-compatible engine and synthetic images.

Restart the local app with `npm run dev`. The database upgrade is already installed; do not run the destructive demo seed against the existing database.
