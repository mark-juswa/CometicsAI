# Oversized generated-look saving

Status: CONFIRMED user scope, 9 November 2026.

Fix the intermittent “Request is too large” error when saving or booking a generated look, then publish the tested application changes to GitHub. Preserve protected AI models, datasets, inference, generation, runtime and deployment resources.

The shared Save Look / Book This Look action must prepare a smaller persisted reference copy when the generated PNG/JPEG exceeds the existing 8 MiB save limit. Prepare this copy only on an explicit save or booking action. Keep images within the limit byte-for-byte unchanged, and keep the generated result, original preview and download unchanged in every case.

Use browser-native image decoding and a bounded canvas (longest edge at most 2048 pixels). Encode a JPEG reference up to 2 MiB, retaining aspect ratio and using a white background for transparency. Try high quality first, then reduce quality/dimensions within bounded attempts. Release canvas memory afterward and show a readable failure if preparation fails. Clearly disclose the smaller saved copy on oversized previews.

Prepare the copy once before existing idempotent save retries so all retries reuse identical bytes. Keep owner access, validation, gallery/storage quotas and database admission unchanged. Do not retry generation or replay appointment creation. Save once, route using the returned saved identity, and attach that identity to the booking. No database migration or live-data rewrite is required.

Acceptance includes reproducing HTTP 413 with a valid image above the old body bound; successful bounded save and booking across Hair, Nails and Makeup; unchanged original data; no extra generation; boundary/base64-padding, fallback, aspect ratio and failure cleanup checks; typecheck/build; protected-source hashes; and a real-browser conversion check using synthetic data only.
