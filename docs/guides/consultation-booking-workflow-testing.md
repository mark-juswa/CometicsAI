# Consultation, booking, completion and reviews: local review guide

2026-10-20, Asia/Manila. Development implemented locally. This guide does not authorize or claim Render deployment, live migration, GPU execution or real-device acceptance.

## What changed

- Consultation Save/Book is now attached to the **selected completed recommendation**, not whichever look is currently being viewed. Select the look, then use **Book Selected Look** in its selected summary. Existing standalone Save/Book actions remain.
- The existing saved generation and appointment reference remain the single image source. Both home dashboards and appointment pages show the saved description/estimate and requested image. Gallery removal still preserves booked references.
- Client home adds Recently Completed, a status/details view and a review form. Completed visits are excluded from Upcoming; full completed history remains under Past/All appointments. Appointment screens refresh when returning to the browser tab.
- Assigned stylists/admins use **Mark as Completed → optional products → Confirm completion**. An assigned stylist is required before completion. Pending or confirmed services can be completed; no new availability or schedule engine is introduced.
- Completion records a server timestamp/actor and up to 20 product lines in one atomic database function. Retry does not add duplicate usage or change the completion time. Cancelled appointments cannot be completed/reopened. Completed appointments cannot be reopened, reassigned, rescheduled or hard-deleted.
- Existing admin controls can still correct a completed service's recorded amount/notes; no new accounting correction ledger is claimed. There is no post-completion product-edit or review-edit workflow.
- One completed-appointment review per owning client, rating 1–5 with optional comment (1000 characters). Client/stylist attribution is derived by the server. An identical retry is accepted; a different second review is rejected. Existing completed appointments with an assigned stylist can be reviewed; missing historical completion times remain unknown.
- Admin → Finance adds Stylist Performance with scheduled Manila date filters (up to 31 days), completed counts, recorded amounts, unpriced counts, average verified rating and review count. Sorting is by completed count/name or average rating/review count/completed count/name. Unrated staff are labeled Unrated. This is not a weighted reputation score or a claim of net profit.

## Products, units and prices

Actual products belong to service completion, separate from immutable AI look descriptions. Select an existing inventory item or enter an unlisted product. Its name/brand can be customized for the actual service. Add an optional brand when creating an inventory item; existing inventory brand can be updated through its admin PATCH API. Actual usage brands can always be entered without changing the catalog.

Quantity (up to 3 decimal places), unit and material cost per that unit in PHP (up to 2 decimal places) are optional. A quantity requires a unit; a cost requires both. Omitted values remain unknown, not zero. Supported explicit units: ml, l, g, kg, piece, pair, bottle, pack, set, application. No conversion between them is inferred. Product records retain their snapshots if a catalog item is renamed/deleted. Staff/admins can view material cost; clients see the product/brand/quantity without internal material costs.

**Stock is not automatically deducted.** Admin stock adjustment continues as before. Inventory unit_price is not copied into material cost, since its acquisition-cost/unit basis is not established. Usage rows support later per-product/brand/unit statistics; a stock ledger, automated inventory reports, payment receipts, payroll/commissions/expenses and net profit remain outside this release.

## Database preparation — separate from deployment

Explicit additive migrations, in order: existing0002 and0003, pending0004_look_details.sql, then new0005_service_completion.sql. The explicit runner includes all four files and uses one transaction per file, with PL/pgSQL statement boundaries preserved. It never runs automatically on web startup. New completion/review functions, historical guards, FK indexes, product tables and inventory brand are in0005.

**Do not deploy this checkout against an unmigrated database:** appointment reads require look_details, completed_at/by and the new tables. No feature flag makes the old schema compatible. No live migration was performed during development.

For manual local acceptance, use an explicitly selected disposable/test database branch and test accounts; never point a development seed at live client records. Keep its connection string private. On that approved test database only, run the explicit migration utility from beautycore with `npx tsx scripts/apply-saved-looks.ts --apply`. Default/`--check` is read-only; `npm run db:check:saved-looks` now also reports workflow readiness. Apply and check modes do not seed users. Avoid db:push for this rollout.

Saved-look flows still require existing SAVED_LOOKS_ENABLED=true and adequate image-storage limits. Existing session/Neon/AI/Kaggle endpoint configuration remains in use; no new secrets, GPU settings or public endpoints are required. Start the current Kaggle demo only when performing actual AI image generation. Fixture tests below do not need it.

## Automated verification

From beautycore:

1. `npm run test:business` — disposable PGlite SQL and DOM interactions; no live database or AI requests.
2. Existing AI adapter/client/jobs/runtime-registry/studio integration suites — signed handles, role/origin restrictions, hosted jobs/busy responses and endpoint discovery.
3. `npm run build` — production bundling and TypeScript checks. `npm run typecheck` can be run separately.

Tests include atomic rollback, duplicate/concurrent requests, cross-client/foreign-stylist denial, cancelled/legacy services, preserved product snapshots and private costs, Manila date boundaries, unpriced services, selected-B/viewed-A booking, both home dashboards and an actual DOM completion/review/report journey. The fixture transport uses real business handlers/store/SQL but synthetic AI responses, not GPU-generated images. PGlite concurrent calls verify the application retry path; multi-connection Neon contention and actual browser/device layout remain release checks.

## Manual acceptance on the test system

1. Client: run a Hair, Makeup or Nails consultation and generate three looks. Select B, view A, then **Book Selected Look**. Confirm the booking preview/service category correspond to B and its description/estimate. Book a future appointment with a chosen stylist. Repeat one case for each feature; missing Makeup prices must remain quote-required.
2. Client home and Appointments: verify the saved image, description, estimate, scheduled date/time, recorded amount and stylist. Reload. Remove the look from My Saved Looks and confirm the booked image remains accessible.
3. Assigned stylist: open the same booking under home/All Appointments. Verify image/details/client; a different stylist must not access the private appointment image.
4. Click **Mark as Completed**. Add one catalog product and one unlisted product/brand. Supply quantity/unit/confirmed unit cost only where known. Confirm completion. Verify the timestamp and recorded products, unchanged stock, and no reopening/reassignment/deletion option. Retry the same request if testing connectivity; it must not duplicate usage.
5. Client: return to the tab or reload. Verify Recently Completed/Past contains the booking and cannot be cancelled. Submit a rating/comment. Reload and confirm one persistent review; other clients and incomplete appointments must not be eligible. Internal material costs must not appear in client responses/UI.
6. Admin: Finance → select the appointment's **scheduled Philippine service date** in Daily Services and Stylist Performance. Verify one completed visit and one review, the correct amount/unpriced value and rating. Adding multiple product lines must not multiply revenue or completed counts.
7. Regression: ordinary appointments without an AI look, cancelled and legacy completed appointments, gallery persistence, standalone Hair/Makeup/Nails generation, Consultation recovery and existing registered Kaggle discovery continue to work.

## Release boundary

Implementation is local only. A separate release must verify the actual Render revision/database branch, rehearse migrations and backup/recovery policy, apply schema before code, then perform browser/client/stylist/admin acceptance. Keep the working Kaggle notebook/bundles and live site intact. The separate experimental AI speed cache remains unchanged and disabled.
