# Booking service context and dynamic availability

Status: CONFIRMED, 9 November 2026. Implements the user's attached booking requirements; protected AI resources remain unchanged.

Persist actual salon services and preset associations under stable service IDs. Bootstrap each preset's primary service from its first supported existing catalog association, retaining other services as manual choices. Retrieve the current database price and category, prefill the saved-look booking form, preserve manual changes during date/stylist refresh, and allow manual selection for unmapped presets. Appointment service identity is stored in an atomic one-to-one appointment_services record; existing appointment rows remain unchanged.

Use exactly 90 minutes in every scheduling method. Generate candidates from each stylist's actual daily start time in consecutive 90-minute steps. If a candidate overlaps a reservation, resume at the conflicting reservation's actual 90-minute end, including off-grid legacy starts (10:00 resumes at 11:30). Fit the full reservation in working hours, omit past starts, release cancelled bookings, and retain working-status/qualification checks and transaction-level locks.

Expose selectable time buttons and an accessible select, selected/unavailable states, loading, errors and empty results. Save-and-book must use the database ID and current service information; request-supplied names/prices are not authoritative for customer bookings. No generation, model, dataset or deployment change is authorized by this application work.
