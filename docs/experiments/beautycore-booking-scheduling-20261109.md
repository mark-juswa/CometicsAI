# Booking scheduling update, 9 November 2026

Status: DONE implementation and configured-database scheduling upgrade; VERIFIED automated checks and production build. GitHub publication is recorded separately in the local publication receipt.

## Delivered behavior

- Every catalog service and new appointment reserves 90 minutes. The calendar loads qualified on-duty stylists and actual pending/confirmed reservations through a private-cache read-only availability endpoint. Half-hour start options disable overlaps, past starts and times that cannot fit within working hours. Staff selection precedes date/time selection and remains selected when a slot is busy.
- A 09:00 booking blocks 09:00, 09:30 and 10:00 for that stylist; 10:30 is the next available boundary. A different available stylist can still be booked. No-preference bookings keep their existing pending-assignment workflow.
- Migration 0010 changes the appointment default and three scheduling functions. Legacy callers also receive 90-minute new bookings. Existing row contents and historical durations stay unchanged; active legacy rows reserve at least 90 minutes, with longer rows preserved at their full duration. Pre-existing overlaps are not moved or erased.
- Saving a look retries up to three total attempts for temporary network/admission/server failures using the exact same payload. The existing owner/style/image-hash admission prevents duplicate saved records, including when the original save committed but its response was lost. Permanent errors are not retried. Generated-result identity is tied to the saved preview, a failed saved-look read has a Retry action, and auth refresh no longer clears a selected service. HTML responses display a readable error. Appointment POST is never automatically retried.

## Verification

- Full application suite: **116 passed, 0 failed**. Includes 90-minute catalog policy, real PostgreSQL-compatible atomic conflict checks, 09:00/10:30 calendar boundaries, independent stylists, cancelled/off-duty behavior, legacy duration preservation and repeat migration safety; lost-response save recovery with one record and no generation; temporary/permanent save errors; and saved-look reload recovery. The first test run exposed two test-fixture mistakes (wrong initial service category and outdated service label), corrected before the final passing run.
- Production build passed, including TypeScript and the new availability route. Local built-app availability smoke returned HTTP 200 with duration 90 and Asia/Manila zone; no real booking or image save was created for verification.
- Configured database migration completed transactionally with exact before/after fingerprints for all nine guarded tables unchanged: 14 users, 9 profiles, 29 appointments, 75 generation rows, 18 inventory entries, 9 specialties, and zero product-usage, reviews or inventory-transaction rows. No seed, row UPDATE or DELETE was performed. Existing archive/payment/work-setting tables are not mutated by this DDL-only migration.
- All 265 protected-source hashes match the baseline. No model, dataset, prompt, generation/inference, RunPod or deployment configuration changed.

## Rollout and limits

The configured database already has the scheduling upgrade. For another environment with the earlier migrations installed, run npm run db:apply:scheduling from beautycore; its transaction rolls back if guarded row contents differ. Merge the GitHub review branch into the branch linked to Render and deploy it to display the new calendar. GitHub publication alone does not update the website. Browser viewport acceptance and the user's exact original save error remain unverified; no external generation was run.

Archived build-log trailing whitespace is normalized; the original local build output is retained.

Evidence: [test log](beautycore-booking-scheduling-20261109/tests.log), [build log](beautycore-booking-scheduling-20261109/build.log), [preservation result](beautycore-booking-scheduling-20261109/migration.log), [scope](../specs/beautycore-ninety-minute-bookings.md).
