# BeautyCore revenue periods and stylist earnings UI — 9 November 2026

Status: DONE for implementation; automated, build, and local authenticated API checks VERIFIED. Real-browser visual acceptance remains NEEDS VERIFICATION.

## Delivered behavior

The admin Dashboard now has a revenue panel with Daily, Weekly, Monthly, and Yearly controls, a reference-date picker, previous-period comparison, completed-service counts, average priced-service value, and an interactive revenue trend. All-time revenue remains visible. Empty periods have explicit empty feedback and zero-filled time buckets; missing prices are flagged separately.

The admin Stylists section is reorganized around earnings and a staff roster rather than permanently open account forms. It displays each stylist's day, month, and year revenue together, with the selected period highlighted. Search, availability/account-status filters, earnings/service/name sorting, summary cards, and separate Add/Edit dialogs retain the existing account-management functionality. Inactive stylists retain their historical earnings in the report.

Earnings and dashboard revenue use the recorded prices of completed services by their scheduled service date. This preserves the existing finance convention. Payment receipts remain a separate report; no payroll, salary, commission rate, or take-home calculation was invented.

## Calendar and aggregation rules

- Reporting dates use `Asia/Manila` regardless of browser or database-session timezone.
- Daily windows run from Philippine midnight to the next midnight and provide 24 hourly chart buckets.
- Weeks run Monday–Sunday with seven daily buckets.
- Months cover the full calendar month, including leap February, with daily buckets.
- Years cover January–December with 12 monthly buckets.
- Previous comparisons use the previous matching calendar period. A zero previous amount has no fabricated percentage; equal values show no change.
- Pending, confirmed, and cancelled appointments do not count as revenue. A completed free service remains distinct from an unpriced service.
- Reports count appointments directly, avoiding multiplication through products or receipt joins. Unassigned completed services remain in salon revenue and are identified separately from stylist attribution.

## Files and API

Paths are relative to `beautycore/`.

| File | Purpose |
| --- | --- |
| `lib/business/revenue-periods.ts` | Validated calendar windows, comparison windows, and shared report types |
| `lib/business/revenue-store.ts` | Read-only summary, time-bucket, and stylist earnings queries |
| `lib/business/store.ts` | Exposes the revenue report through the existing business store |
| `lib/business/api.ts` | Adds validated calendar-period reporting to the existing admin-only performance endpoint |
| `components/revenue-report.tsx` | Shared period controls, abort-safe report loading, revenue panel and interactive chart |
| `components/stylist-account-dialog.tsx` | Separate, accessible Add/Edit dialogs using the existing staff API |
| `app/admin/stylists/page.tsx` | Redesigned earnings roster and staff management |
| `app/admin/dashboard/page.tsx` | Period-selectable revenue panel replacing the fixed revenue card |
| `app/(public)/booking/booking-form.tsx` | Cleans up an existing delayed redirect when the page unmounts; the longer UI tests exposed the stale navigation |
| `next.config.ts` | Disables only development filesystem caching after repeated observed Turbopack persist/compaction errors; production cache defaults and AI configuration remain unchanged |
| `tests/revenue-report.test.ts` | Calendar, timezone, aggregation, authorization, and empty-report tests |
| `tests/business-ui.test.mjs` | Period-switching, roster earnings, account editor, and existing workflow checks |
| `package.json` | Includes the new report tests in the existing sequential business suite |

The existing endpoint now accepts:

```text
GET /api/admin/stylist-performance?period=day|week|month|year&date=YYYY-MM-DD
```

It returns the selected calendar window, summary, zero-filled chart series, and staff metadata with selected/day/month/year earnings. Authentication, fresh admin role checks and `private, no-store` remain enforced. Invalid dates, unsupported periods, and mixed calendar/custom-range inputs are rejected. The existing `from`/`to` custom report and its 31-day limit remain compatible for the Finance page.

No new database table, column, migration, receipt, commission field, customer record, account, or appointment was added or changed for this task. New reporting queries are read-only. Account editing tests use an isolated fixture, not the configured database.

## Verification

- Full business suite: **88 passed, 0 failed**.
- TypeScript check and final production build passed.
- Tests verify Manila midnight, Monday/Sunday boundaries, leap months and years, full-year ranges, inactive staff, missing/zero prices, excluded statuses, unassigned service totals, empty periods, invalid inputs and admin-only access.
- UI tests switch all four dashboard periods, verify time-bucket counts and actual fixture amounts, inspect the three earnings columns, edit a fixture account in the new dialog, and open/cancel account creation. Existing consultation, saved-look, appointment, payment and availability tests also pass.
- Authenticated local API checks before and after the final server restart returned HTTP 200 for all four periods. For reference date 2026-11-09: 24 daily, 7 weekly, 30 monthly and 12 yearly buckets; each series summed to its displayed total. The real report returned four staff records.
- After restart, anonymous session and admin sign-in returned HTTP 200 JSON; `/admin/stylists` and `/admin/dashboard` returned HTTP 200. Test credentials and cookies were not printed.
- Protected-source manifest: **265 checked, zero changed hashes**. No models, datasets, weights, LoRA adapters, inference prompts/parameters, Kaggle resources, generation requests or protected AI sources were changed or executed.

The local development server was paused during the production build and then restarted on port 3000. It remains running. No cloud deployment was performed. The connected preview tools did not provide a local browser/viewport visual review; final desktop/mobile visual acceptance is still pending.
