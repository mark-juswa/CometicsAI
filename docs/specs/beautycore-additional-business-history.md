# BeautyCore additional business history and private image reuse

Status: CONFIRMED scope; implementation and database installation VERIFIED on 9 November 2026. Visual and real external generation acceptance remain separate.

The user requests removal of login demo credentials, selectable admin client histories and transactions, automatic availability-based appointment confirmation, persistent consultation photos/results and reuse, a stylist work switch, and consistent admin/stylist UI. The user explicitly protects existing models, datasets and generation behavior.

The existing Next.js/React/Neon/Drizzle architecture remains authoritative. New customer history and receipt records are business data, stored with the existing database image approach. Protected AI forwarding and generation code remains unchanged; the authenticated application route archives accepted state and results around that boundary. A file selected from private history enters the existing photo upload flow without changing the inference request.

Only customers may browse their image/session history or submit a private look with a new appointment. Administrators receive relevant client/transaction metadata and the specific image already submitted by the customer for an appointment. Stylists receive only assigned booking images and their own work settings.

Weekly work settings default OFF without a fabricated real schedule. A selected active, qualified stylist automatically confirms only within configured Philippine working hours, with the entire catalog duration clear of existing active bookings. No-preference requests remain pending. Shared database locks serialize schedule availability changes and competing assignments; switching OFF preserves existing appointments.

Payment receipt amounts, service prices and appointment status remain distinct. Historical prices do not create fabricated receipts. Receipt entry is admin-only, idempotent, and capped at the recorded balance.

Additive migrations 0008 and 0009 install the necessary tables/functions. The upgrade command protects and checks existing rows inside the transaction. Detailed paths, endpoint contracts, results, database preservation evidence and operational limits are in `docs/experiments/beautycore-additional-enhancements-20261109.md`.
