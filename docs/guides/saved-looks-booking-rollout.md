# Saved looks, booking references and daily services: rollout guide

**2026-10-17 — implementation DONE; local verification VERIFIED; production database migration VERIFIED; Render deployment PENDING.**

**Current rollout:** The Supervisor approved rollout and explicitly requested skipping the new backup. Both additive migrations are applied to the existing database. Server-side counts/checksums confirm that all six tables' existing records and original fields remain unchanged. No live client/account rows were exported. The first migration attempt failed before committing because Neon HTTP queries require one statement at a time; the corrected atomic-batch runner passed two new regression tests. Combined 86 tests and production build pass. [Rollout evidence](../experiments/saved-looks-render-rollout-20261017.json).

The database is ready for the new website code. Render still requires its environment settings and a manual deployment. In the service dashboard, add `SAVED_LOOKS_ENABLED=true`, `SAVED_LOOKS_CLIENT_LIMIT=20`, and `SAVED_LOOKS_STORAGE_BYTES=134217728`; choose **Save only**, then **Manual Deploy → Deploy latest commit** from the published `codex/render-kaggle-demo` branch (release code `80ef11a`). Do not change the existing database or AI credentials. This setup uses the existing Kaggle notebook/models/registration unchanged. Real-image limits, loaded Render memory and client-device acceptance remain to be checked during rehearsal.

## What is implemented

- Completed Hair, Makeup, Nails and Consultation results offer **Save Look** and **Book This Look**. Saving uses the already generated image and never starts another AI request. Development placeholders cannot be saved.
- **My Saved Looks** provides feature/date filters, pagination, view, download, booking and removal. Saving twice reuses the same image record for that client/style/result.
- Booking from a look opens the usual booking form with the image and correct service category. The client still chooses the salon service, time and stylist and confirms. Normal bookings remain supported.
- Appointments reference the existing `ai_generations` row instead of copying the image. Clients see their own references; assigned stylists and admins can open a booking's reference. Assignment changes update stylist access.
- Removing from Saved hides the record but retains the image, including an existing booking's reference. Image content cannot be edited in place. Hidden images still consume storage.
- Admins can assign a stylist and confirm the recorded whole-peso amount. **Makeup Application** is available with **Price to be confirmed**, pending business confirmation of the offering before release.
- Admin Finance includes **Daily Services**, grouped by scheduled service date and stylist, including Unassigned. Only completed appointments contribute to **Recorded completed-service amount**. Unpriced records are counted separately. This is not a payment ledger.

Reports and booking inputs use **Asia/Manila**. Existing timestamp-without-time-zone values are interpreted using the application's existing UTC storage convention. No historical dates were shifted; confirm a known historical booking before production signoff. The report date is not the time someone clicked Complete.

## Persistence and limits

Images are stored privately in the existing Neon PostgreSQL `ai_generations` table. New saves contain the generated preview, public style ID/name and ownership metadata; they do not require storing the original uploaded photo or an invented model prompt. Authenticated image endpoints check current account roles and booking assignment and return private, noncached responses. Gallery listings contain metadata, not base64 images.

| Configuration | Default | Meaning |
| --- | --- | --- |
| `SAVED_LOOKS_ENABLED` | `false` | Must be exactly `true` to allow the new saved-look operations and look-linked bookings. |
| `SAVED_LOOKS_CLIENT_LIMIT` | `20` | Active saved records per client; supported range 1–100. |
| `SAVED_LOOKS_STORAGE_BYTES` | `134217728` | 128 MiB budget for existing generated/source image text plus new generated-image text; supported range 1–256 MiB. |
| `DATABASE_URL` | Existing private configuration | Same Neon database used by appointments and account authentication. |
| `RENDER_EXTERNAL_URL` | Existing Render-provided origin | Same-origin write protection; must match the public HTTPS site origin. |

Each new image must be a valid single PNG/JPEG, at most **8 MiB decoded**, at most **4096 pixels per side** and 16,777,216 pixels total. Base64 storage is larger than the decoded file. A maximum of two save payloads are admitted concurrently per application process. A PostgreSQL transaction lock serializes quota/deduplication decisions across processes. The budget includes legacy image text and retained hidden images; it excludes other database data/indexes and is not a provider storage-quota guarantee.

A full client gallery or storage budget returns a controlled error without erasing the current generated preview. Repeating an already saved result does not consume another slot. Gallery removal is not physical deletion. Do not promise unlimited saving.

Save accepts a validated preview from the authenticated browser. It does not cryptographically prove that the image originated from the AI model. No remote image URL is fetched by the save endpoint.

## Local verification and reproducible commands

From the repository root:

```powershell
python scripts/check_saved_look_catalog.py
cd beautycore
node --experimental-test-module-mocks --import tsx --test tests/ai-runtime-registry.test.ts tests/ai-adapter.test.ts tests/ai-client-flow.test.ts tests/ai-jobs.test.ts tests/ai-studio-integration.test.ts tests/business-workflows.test.ts tests/business-ui.test.mjs tests/finance-stats.test.mjs tests/saved-look-migrations.test.ts
npm run build
```

The final combined run passed **86 tests**: 58 retained AI tests, 17 business API/database tests, seven DOM UI tests, two actual admin-statistics route tests and two migration transport/rollback tests. The production build, including TypeScript checking, passed. `npm run test:business` runs the 28 business tests alone. Tests use isolated PGlite PostgreSQL fixtures and synthetic images; they do not mutate Neon or call a GPU service.

The DOM tests exercise the real components/API handlers, including Nails generation fixture → save → booking → assigned stylist preview → completion → daily report. They also cover save failure/retry without another inference request, client gallery removal, anonymous login return, admin assignment/amount, ownership, roles, byte/dimension bounds, quotas, idempotency, retention, date boundaries and completed-only totals. This is automated component/integration evidence, not live-browser visual or real-device acceptance.

The old `npm run lint` script/configuration is not a working Next.js lint check in this checkout; lint is not claimed as passed. No unrelated dependency-audit upgrade was performed.

## Production rollout procedure

The migration has already been applied for this rollout; keep the commands below for future environments. The Supervisor waived the new backup in this rollout.

**Do not deploy the new appointment routes before the migration.** Those routes join the new saved-look fields even when new saving is disabled. The flag alone cannot make the new code compatible with the old schema.

1. Review the feature diff and this guide. Keep Render automatic deployment off. Confirm the exact source branch/commit and the intended Neon project/environment privately.
2. Prepare a recoverable Neon backup/branch using the database owner's existing process. Rehearse both migration files and application acceptance on a disposable copy first. Do not use the seed script: it deletes data.
3. From `beautycore`, with the intended database configured privately, run the **read-only** preflight:

   ```powershell
   npm run db:check:saved-looks
   ```

   The development preflight reported `applied: false` and **10,964,227 bytes** of existing image text. This is a point-in-time aggregate, not a current provider capacity guarantee. Check current Neon total storage/plan capacity, retained-image growth and Render memory before enabling saving.
4. After migration approval, explicitly run:

   ```powershell
   npx tsx scripts/apply-saved-looks.ts --apply
   npm run db:check:saved-looks
   ```

   The utility runs `0002_saved_looks.sql` and then `0003_saved_look_admission.sql` as separate atomic transactions, each containing one HTTP query per explicitly marked SQL statement. PostgreSQL must commit the added Makeup enum before using it in the save function. Confirm `applied: true`; stop on errors. The migrations are additive and tested for repeat execution. They never run automatically on app build/start. Do not substitute `db:push` or `db:seed`.
5. Deploy the reviewed application commit to Render deliberately, retaining the existing database, authentication, AI backend and dynamic Kaggle registration configuration. Keep `SAVED_LOOKS_ENABLED=false` during initial verification. No Kaggle update is required.
6. Once capacity and image limits are accepted, set `SAVED_LOOKS_ENABLED=true`, `SAVED_LOOKS_CLIENT_LIMIT=20`, and `SAVED_LOOKS_STORAGE_BYTES=134217728` unless explicitly revised after review. Restart/redeploy for environment changes.
7. Run the acceptance checklist below with designated test accounts. If something fails, disable new saving and retain the schema and existing image data while investigating. Do not delete live bookings to repeat a test.

The flag gates saving, gallery operations and new look-linked bookings. The buttons are currently rendered in the web app even while the flag is off and will show the controlled unavailable response. Existing booking image references remain readable for authorized users.

## Release acceptance checklist

Use approved test accounts and images; do not copy private customer photos into issue trackers or this repository.

- Client: generate and save one Hair, Makeup, model-backed Nails, renderer Nails and Consultation result. Confirm correct image/style and no generation request when saving or booking it. Test actual returned PNG/JPEG sizes against the bound.
- Persistence: reload, sign out/in, open a second browser/device, then stop Kaggle. Saved images and existing booking references should still load from Neon. Restart the web service and verify again.
- Booking: use Book This Look from result/gallery, confirm a matching service/time/stylist, and check the exact reference in client and assigned-stylist cards. Also create a normal booking without a look. Confirm Makeup's unknown-price label and the business-approved service name.
- Permissions: another client/unassigned stylist cannot fetch the image. Reassign a booking and verify old/new stylist access. Remove a booked look from Saved and confirm the assigned stylist can still view it.
- Admin: confirm an amount and complete a test appointment. Reconcile daily details and summary by stylist/date, including Unassigned and null/zero prices. Pending/cancelled amounts must not increase the completed-service total. Verify a known existing booking and a Manila-midnight case.
- Failure: test a save error/full gallery while preserving download and the preview. Check there is no automatic inference retry. Existing busy-429 behavior and serialized generation must remain intact.
- Device/layout: inspect the three portals on client devices and phone widths, including full-image dialogs and report scrolling. No live visual/device walkthrough was performed during this development pass.
- Capacity: measure the actual Render process while saving representative large outputs and concurrent requests. An isolated validator probe reached about **209 MiB RSS** for two synthetic 4096×4096 PNGs from an 80 MiB baseline; it is not a loaded Next.js/Render memory acceptance test.

## Rollback and handover

Keep the last working application revision available. To stop new saves, set `SAVED_LOOKS_ENABLED=false`. To roll the app back, deploy the previous reviewed application revision and **retain** the added schema, enum values and saved images. Do not drop columns, remove Makeup from the PostgreSQL enum, reseed accounts or physically delete saved references as a rollback step.

A client still starts the existing private Kaggle notebook for fresh AI generation and waits for its normal website-connection acknowledgement. Saved looks and bookings do not depend on a running GPU session. Existing Kaggle session/quota and model-quality limits remain.

This release adds the web account workflow only. Native mobile Save/Book/gallery screens are not implemented; the existing mobile AI generation contracts remain unchanged. Payments, slot-collision scheduling, completion-date accounting, physical image deletion and unbounded production image hosting are outside this slice.

[Implementation evidence](../experiments/saved-looks-booking-development-20261017.json) · [approved design and original audit](../specs/0010-saved-looks-booking-daily-services.md)
