# BeautyCore portal interface scope

Status: CONFIRMED user scope, 9 November 2026. Implementation evidence is in [the report](../experiments/beautycore-portal-ui-20261109.md).

Improve Admin Appointments and Finance, every Stylist section, and Client Dashboard, Profile, My Saved Looks, and Consultation History. Preserve the purple/gold identity while making summaries, filters, details, and primary actions easier to distinguish. Support narrow screens and keyboard access.

Client AI Consultation, Nail Studio, Hair Studio, Makeup Studio, and Appointments are excluded from the page redesign. Consultation History is a private archive view, distinct from AI Consultation. Do not modify protected models, datasets, inference/generation code, or provider configuration. No database migration, production deployment, or account replacement is part of this request.

## Required behavior

- Admin appointments: concise booking register, Philippine date filters, search, status/service/stylist filters, sorting, pagination, and a selected-booking details dialog. Retain selected booked image, notes, assignment, amount correction, rescheduling, completion/product records, and customer-history access. Confirm cancellation and permanent deletion; keep existing closed-record and receipt guards.
- Stylist: workday summaries and availability, expandable assigned visits with completion controls, a searchable assigned-client directory, grouped reference service pricing, and an improved profile form. Existing role and image permissions remain authoritative.
- Client: clearer dashboard actions and visit summaries, profile information/preferences, image-first saved collection, and private consultation archive cards and conversations. Continue existing save/book/download/remove workflows.
- Finance: separate revenue overview, payment receipts, daily services, and team performance. Retain service and booking-status summaries. Service revenue is recorded completed-service value; receipts and compensation are separate concepts. Booking counts in the popular-service list include all statuses.
- Home services: `/services#hair-design`, `/services#nail-studio`, and `/services#face-laser` select their actual matching menu. Category links remain shareable and respond to hash and browser-history changes.

Use existing APIs and records. UI verification must not create, edit, cancel, or delete real business records. Exercise mutations only in the isolated test database.
