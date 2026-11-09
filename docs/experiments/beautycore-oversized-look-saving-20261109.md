# Oversized look saving, 9 November 2026

Status: DONE implementation; VERIFIED automated checks, standalone typecheck, production build and real-browser conversion. GitHub publication is recorded in the local publication receipt.

## Cause and correction

The shared save endpoint accepts at most 8 MiB of decoded image bytes and a corresponding bounded JSON/base64 body. The original save action sent the entire generated PNG/JPEG. A valid 12,605,186-byte synthetic PNG reproduced HTTP 413 with the exact screenshot message, Request is too large. Temporary retries cannot resolve that permanent size rejection.

The explicit Save Look and Book This Look actions now prepare a smaller persisted reference only when the original exceeds the existing limit. Browser-native canvas retains aspect ratio, caps the longest edge at 2048, tries high JPEG quality first and reduces quality/dimensions until the copy is at most 2 MiB. Transparent areas use white. The generated result and its existing preview/download are never replaced. Accepted-size originals remain byte-for-byte unchanged. A short notice explains the smaller saved reference.

The copy is prepared once before existing save retries, which therefore reuse identical bytes and retain existing hash-based admission. Save then Book reuses one durable saved identity. Server image decoding, owner access, quotas, booking rules and the protected generation flow remain intact. A shared limit constant keeps the browser save contract aligned with the unchanged server cap. Canvas memory is released after success or failure.

## Verification

- Full application suite: **124 passed, 0 failed**. Three new studio flows reproduce 413 with the original valid oversized PNG, save a bounded JPEG copy, preserve original data, avoid generation, reuse one save and complete an appointment linked to that saved look. Five image-preparation checks cover exact byte/padding boundaries, unchanged normal PNG/JPEG images, aspect ratio, white alpha background, quality/dimension fallback and failure cleanup. Existing scheduling test typings were corrected so standalone TypeScript checks the full test tree.
- Standalone typecheck and final production build passed. Browser-only preparation imports no server image-processing library.
- An isolated real-browser test used the actual transpiled preparation module and real server image validator: original PNG 12,605,186 bytes -> HTTP 413; browser JPEG copy 25,337 bytes, 2048 by 2048 -> HTTP 200. The original data stayed unchanged. The synthetic image was a flat color; the automated fallback tests separately cover difficult size thresholds. Studio DOM tests use a canvas facade plus real PNG/JPEG bytes and an isolated PostgreSQL-compatible database. No claim of physical iPhone/Safari acceptance is made.
- All 265 protected-source SHA-256 entries match the existing baseline. No model, dataset, prompt, inference, generation, RunPod or deployment file changed. No live database record, schema, account, booking or image was modified by this task. No migration is needed.

## Rollout

Merge the review branch into the branch deployed by Render, then build/deploy it to expose this browser-side fix. The previously merged scheduling commit remains included. GitHub publication alone does not prove website deployment. Existing stored images are untouched; a new oversized saved reference may be smaller than the original image offered by the active preview download.

Evidence: [tests](beautycore-oversized-look-saving-20261109/tests.log), [typecheck](beautycore-oversized-look-saving-20261109/typecheck.log), [build](beautycore-oversized-look-saving-20261109/build.log), [browser check](beautycore-oversized-look-saving-20261109/browser-check.json), [scope](../specs/beautycore-oversized-look-saving.md). Archived logs normalize trailing whitespace only.
