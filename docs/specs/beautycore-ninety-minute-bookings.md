# Ninety-minute appointments and reliable look booking

Status: CONFIRMED user scope, 9 November 2026.

Every new service booking reserves 90 minutes. For a selected stylist, a 09:00 appointment prevents overlapping starts at 09:00, 09:30 and 10:00; 10:30 becomes available if working hours permit. Other stylists remain independently available. Keep the existing Philippine time zone, qualified-staff rules, availability toggle and atomic database conflict checks. Use a half-hour calendar grid and fit the full appointment inside working hours.

Preserve all existing records. Active legacy bookings reserve at least 90 minutes for conflict detection; longer legacy reservations retain their full duration. Do not move appointments, rewrite history, seed accounts or reset data. An additive migration changes the scheduling functions and default only.

The user reports an intermittent error while saving a generated look before booking. Retry only temporary, idempotent image-save failures using the same payload. Never retry generation or blindly replay appointment creation. Keep permanent gallery, storage, validation and permission errors visible, provide a retry for loading a saved look, preserve its identity across auth refresh, and route only after a valid saved identity is returned. No exact original error text was supplied, so root-cause attribution remains unverified.

Protected models, datasets, generation code, prompts, runtime and deployment files remain unchanged. Publish the tested application changes to the existing GitHub review branch; merging and provider deployment remain separate steps.
