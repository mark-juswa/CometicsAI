# BeautyCore portal refinements, 9 November 2026

Status: VERIFIED automated behavior, typecheck and production build; prepared for publication on the existing enhancement review branch. No database migration or live data mutation is required.

## Delivered scope

- Consultation History generated looks have a Download image action. The authenticated image endpoint returns the original PNG/JPEG as an attachment with a safe filename. Owners can download an archived result even before saving it to their lookbook. Other clients and unassigned staff retain the existing access restrictions.
- The men's haircut entry is hidden only in the public Services price list reached from Home. The homepage itself has category links rather than a detailed price table. The shared catalog, booking option, staff reference menu, saved estimates and existing records remain intact, following the user's clarification.
- Hair, Makeup and Nail studios offer Choose an existing image. The private picker supplies a normal File to each studio's existing photo-selection handler. Selecting an image does not start generation or change AI settings.
- Client and Stylist portals have a fixed booking alert bar. It shows upcoming pending/confirmed bookings scoped to the signed-in owner or assigned stylist. Notifications refresh every 30 seconds while visible, on focus, and on appointment-update events. Read markers are stored per account in the current browser. This is an in-app alert, not email or OS push.
- Alert links open the relevant appointment. Existing filters are cleared as needed; a stylist's linked visit is opened on the correct pagination page. The alert menu closes on outside click/Escape and remains scrollable on smaller screens.
- In Admin Stylists, clicking a stylist's name opens completed service history with date filters, pagination, client, service, scheduled date, completion date when known, recorded amount and rating. Summaries distinguish unpriced and free services. This endpoint is admin-only and exposes no private photo gallery.

## Verification

- Full application suite: **105 passed, 0 failed**. Added coverage for account-scoped booking alerts and their assignment/cancellation changes; per-account browser read markers and links; a linked appointment on the second page; admin-only stylist service history; original private image downloads; each of the three studio pickers without generation; and public-price-list hiding while retaining booking availability.
- Final production build passed, including TypeScript compilation and generated routes. The standalone typecheck also passed before the final test-only adjustments.
- All 265 existing protected-source SHA-256 entries match their baseline. No model, dataset, weights, prompts, AI forwarding/generation implementation, Runpod configuration or release metadata was modified.
- Mutating checks use isolated PGlite fixtures. No real booking, receipt, profile or image record was created or changed by verification. Existing schema tables are reused.
- Browser viewport visual acceptance remains unverified; no screenshot-based claim is made. Layout CSS and semantic interactions were checked through the build and DOM tests.

The refinements preserve earlier portal changes. The latest clarified scope replaces the initial broad catalog removal: only public price presentation changes. The local preview was restarted on port 3000 after build. Publication does not itself merge into main or redeploy the website.
