# BeautyCore calendar revenue and stylist earnings

Status: CONFIRMED user scope; implementation, automated tests, build, and local authenticated read API VERIFIED on 9 November 2026.

The user requests daily/monthly/yearly earnings in the Admin Stylists section, an improved stylist-management interface, and daily/weekly/monthly/yearly revenue on the Dashboard.

Use the existing completed-service recorded-price convention and Philippine scheduled service dates. No salary or commission settings exist, so report each stylist's attributed service revenue explicitly. Do not fabricate take-home pay or derive payment receipts from appointment prices.

Calendar periods are day, Monday–Sunday week, full month and full year, anchored by a chosen date. Preserve all-time revenue and the existing custom-range Finance report. Use the existing admin-only performance endpoint and business store; no schema change is necessary.

The Stylist page prioritizes a searchable, sortable, filtered earnings roster. Show day/month/year amounts together and keep account creation/editing in separate dialogs. Preserve existing specialties, account status, work availability and historical inactive-staff earnings.

The dashboard provides period controls, date selection, previous-period comparison and a real data trend chart. Loading, invalid-date, empty, unpriced and failed-report states must remain distinct. Backend authorization and timezone boundaries are tested; protected AI resources and business records remain unchanged.

See `docs/experiments/beautycore-revenue-ui-20261109.md` for exact files, evidence, API parameters and visual-acceptance limitations.
