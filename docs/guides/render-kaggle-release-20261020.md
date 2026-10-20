# BeautyCore workflow + Nails optimization release

2026-10-20, Asia/Manila. User explicitly authorized release to Render and Kaggle. This supersedes the prior no-deployment boundary for this release only. Automatic endpoint registration, existing credentials, models and private input datasets remain in use.

## Current release contents

The web release includes saved descriptions/catalog estimates, Market Trends removal, selected-look booking, both home dashboard previews, controlled service completion/products, client reviews and admin stylist performance. It reuses existing generations, appointments and inventory.

The new **render_kaggle_optimized_demo.ipynb** applies a reviewed source overlay in a fresh extracted workspace and enables **AI_PROMPT_CACHE=1 / AI_PROMPT_CACHE_SCOPE=nails / AI_INFERENCE_PROFILE=0** only in the GPU worker. Hair/Makeup bypass the performance wrapper entirely. Model-based Red/Black Nails, including consultation requests, reuse only fixed public prompt encodings across crops; renderer styles retain their existing path. No user photo, generated image, chat or private prompt is cached. Model weights, adapters, seeds, steps, dimensions, guidance and quality settings are unchanged.

The supplied application comparison observed Red196.354→172.310s and Black194.345→162.306s with exact paired images. These are one-pair observations, not a universal latency guarantee. Global caching regressed new Hair/Makeup, so this release explicitly does not enable that policy. The scoped policy has local routing/cache tests; fresh live GPU/browser acceptance is still required.

Original render_kaggle_client_demo.ipynb and both private binary inputs remain unchanged as fallback. New source is hash-checked and installed only after the original bundle/environment/model checks, immediately before worker startup. The original source manifest is not rewritten; an additional release record identifies overlay hashes. No new datasets or Secrets are needed.

## Database

Additive migrations0004and0005 were explicitly applied with schema-only verification: applied=true, workflowApplied=true. No seed, client-record export, record fingerprints or application record writes were performed. The existing backup waiver was retained. Automatic approval review blocked an optional local export of record-derived hashes before execution; no such export occurred. Accordingly, exact live record preservation was not independently fingerprint-verified in this release. Disposable migration tests verify legacy compatibility and rollback.

The explicit command used is `npx tsx scripts/apply-saved-looks.ts --apply --schema-only`. The read-only check is `npx tsx scripts/apply-saved-looks.ts --check --schema-only`. Do not apply again just to start Kaggle. No automatic startup migration or db:push is needed.

## Render: one-time release

1. Open the existing beautycore-demo service. Keep repository mark-juswa/CometicsAI, branch codex/render-kaggle-demo, root beautycore and the existing build/start commands.
2. Confirm **SAVED_LOOKS_ENABLED=true**. If missing, add it once. Keep DATABASE_URL, SESSION_SECRET, AI_CONSULTATION_HANDLE_SECRET and AI_BACKEND_API_KEY unchanged. Keep **AI_ENDPOINT_MODE=registered**. Do not copy a temporary tunnel URL into AI_FASTAPI_URL.
3. After the release commit is present on the deployment branch, choose **Manual Deploy → Deploy latest commit**. If saving the environment already triggers that release build, allow that build to finish instead of starting another.
4. Wait until the release is **Live**. Verify /api/health returns200. Unauthenticated GET /api/admin/stylist-performance should be rejected with401, demonstrating both route presence and access protection. A generic health200 alone does not identify the release or prove AI readiness.

No Render API credential/browser control is available to this agent session, so the dashboard deploy must be triggered by the operator. GitHub publication and database readiness are separately verified in release evidence. Official deployment reference: https://render.com/docs/deploys.

## Kaggle: start the optimized service

1. Make a **private copy of the tested pinned notebook**; preserve the old notebook. Use a unique title such as BeautyCore Optimized Demo20261020. Import the local notebooks/render_kaggle_optimized_demo.ipynb into that copy. Confirm the tested image remains pinned; a fresh Latest-image notebook is not equivalent.
2. Attach exactly these same two private inputs: cosmetics100/capstone-train002-20260928-v1 and cosmetics100/render-kaggle-cpu-20261009. No new bundles to upload.
3. Enable Internet and the tested T4 configuration. Enable existing Secrets **AI_BACKEND_API_KEY**, **AI_REMOTE_API_KEY**, **GEMINI_API_KEY**. The backend key must still match Render; do not enter keys in notebook code or messages.
4. Run the three code cells once, in order. Cell1 verifies/extracts the inputs and stages the new source. Cell2 prepares CPU/model environments, starts the optimized GPU worker and authenticated API, then registers with the website. Cell3 reports status.
5. Wait for **CONNECTED TO WEBSITE: https://beautycore-demo.onrender.com**. Keep the Kaggle session running. Do not rerun setup while services are active. No per-run Render configuration is required.

Kaggle startup includes package/model download and is not the image-generation latency benchmark. If a host/package pin fails, keep the guard and return the error; do not bypass it or silently change packages. Existing private input access is still required when handing the notebook to the client. Official notebook reference: https://www.kaggle.com/docs/notebooks.

## Rehearsal before client handoff

Run one Hair, Makeup, model Nails (Red or Black), renderer Nails, and a complete three-look consultation, one request at a time. Confirm generation completes and images preserve quality; timings depend on GPU/setup/case. Then select a completed look, book it with a stylist, verify both dashboards, record actual products on completion, submit one client review and check the admin scheduled-day figures. Follow consultation-booking-workflow-testing.md for the detailed checklist.

This session cannot claim live Kaggle/browser generation until the operator runs the notebook and returns its connection/result evidence. Do not claim the website deployment is Live until Render confirms the release revision.

## Fallback

If the optimized worker fails, stop that new session and run the original tested private notebook with the original two datasets/Secrets. Its signed registration replaces an expired session automatically. Do not start two workers or change Render to an old temporary tunnel URL. Keep the additive database schema on a web rollback; do not drop data. A Render rollback may remove new UI until the release is repaired, while existing accounts/bookings remain in their original tables.
