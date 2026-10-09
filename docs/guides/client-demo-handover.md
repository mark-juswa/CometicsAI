# BeautyCore: client demo operation and handover

**Purpose:** run the deployed Render website with Kaggle providing AI compute for scheduled demonstrations. The client needs a browser and an internet connection, not a local GPU or Python installation.

**Status, 2026-10-09:** Render is available; the last Kaggle tunnel returned HTTP 530. The corrected client starter passes 27 local startup/recovery tests. It has **not yet been run as a complete fresh Kaggle session or on the client's account**. Do not describe the handover as fully verified until the rehearsal below passes.

Website: https://beautycore-demo.onrender.com

## What caused the reported error?

A Render website health response of 200 means the website process is available. It does not mean the separate Kaggle AI service is available. The recorded Kaggle URL returned 530 while Render returned 200, which explains current AI unavailability and is consistent with stopping the Kaggle session or losing its tunnel. The probes cannot identify exactly which Kaggle process stopped or prove that every earlier 502 had this cause.

A generation already accepted by Kaggle continues after the user leaves the page. The current web consultation starts its three recommendations sequentially; navigating away does not explicitly cancel its asynchronous batch. The facade allows one generation at a time across Hair, Makeup and Nails. An overlapping request is rejected with 429, not queued. Switching services alone does not establish the cause of a 502.

During a demo, wait for all three consultation results before starting another feature. If status is uncertain, use Check status rather than repeatedly pressing Generate. Closing a page is not a server cancellation. Restarting Kaggle loses photos, consultations, jobs and results stored in that process; start a new consultation afterward.

## Choose who will operate Kaggle

**For the nearest demonstration:** you operate the existing Kaggle account and Render service. Start AI before the client's appointment, update Render, verify real generation, and give the client the website link. The client uses the site on their device. This avoids an account transfer immediately before a demo, but still depends on you starting the GPU session.

**For independent client operation:** provide a private copy of the tested pinned notebook, access to both private input datasets, their own Kaggle GPU access, and authorized access to update the Render service environment. They enter their own Gemini key and backend/GPU keys into Kaggle Secrets; the backend key must match Render. Notebook/dataset sharing does not substitute for checking actual access under the client account. Do not share your account password. If handing over the entire project rather than demo operation only, also arrange repository, Render and Neon ownership/access explicitly; a website link does not transfer those resources.

## Files and private inputs to provide

- `notebooks/render_kaggle_client_demo.ipynb`: corrected, self-contained starter; three code cells and an explanation cell. No secret values or saved outputs.
- This guide and `docs/guides/render-kaggle-demo.md`: client instructions and detailed maintainer reference.
- Private dataset `cosmetics100/capstone-train002-20260928-v1`, containing `capstone_train002_20260928_v1.bin`.
- Private dataset `cosmetics100/render-kaggle-cpu-20261009`, containing `render_kaggle_cpu_20261009.bin`.

Keep the existing SERVER notebooks and these original bundles as fallback. The new starter does not retrain models or replace the uploaded archives. It embeds the corrected runner, uses isolated CPU pip installation and `MPLBACKEND=Agg`, and uses a new working folder so retained files do not trigger the earlier extraction error. It refuses another startup while worker ports are active.

## One-time Kaggle setup

1. Make a **private copy of the already tested pinned notebook**. Use a unique title, for example `BeautyCore Client Demo 20261009`.
2. Replace its three code cells with the three code cells from `render_kaggle_client_demo.ipynb`. Do not run the old recovery cells as well. If importing the file into a new notebook, first check that the import/copy retained the tested environment; importing alone does not prove this.
3. Attach exactly one copy of each private binary input listed above.
4. Enable Internet and the tested T4 GPU configuration.
5. In Add-ons → Secrets, enable the following exact names for this notebook:

| Kaggle Secret | Requirement |
| --- | --- |
| `AI_BACKEND_API_KEY` | At least 32 characters; exactly the same private value as Render's `AI_BACKEND_API_KEY` |
| `AI_REMOTE_API_KEY` | At least 24 characters; used inside Kaggle between API and GPU worker |
| `GEMINI_API_KEY` | Valid Google AI Studio key for Consultation |
| `HF_TOKEN` | Only if the pinned model download requires authentication |

6. Run Cell 1. It verifies both archives and checks the GPU host against the original reviewed environment before starting package installation. The reviewed host is Python **3.12.13**, Torch **2.10.0+cu128**, CUDA **12.8**, **Tesla T4**. The runner also requires at least **30 GiB host RAM**. A newer default Kaggle image previously failed this compatibility gate. If Cell 1 reports a mismatch, use the tested pinned copy; do not remove the check or replace Torch to force startup.
7. Run Cell 2 once. It installs the isolated CPU dependencies, loads the GPU model, starts the private API and creates the authenticated public tunnel. Wait until it prints `READY_FOR_REHEARSAL` and `Render AI_FASTAPI_URL: https://...trycloudflare.com`.
8. Run Cell 3 to show status and the current URL. Save a version of the working notebook only after checking that its source/output contains no secret values. A saved version is a record, not an always-running server.

**Needs verification:** copying/importing the pinned environment into the client's own account and actual GPU access. The original runtime/model checks remain authoritative.

## Automatic connection: one-time upgrade

The approved automatic registry is implemented. The maintainer applies `beautycore/db/migrations/0001_ai_runtime_endpoints.sql` once, deploys the current branch and sets `AI_ENDPOINT_MODE=registered` once on Render. `AI_BACKEND_MODE=kaggle` and the existing shared backend key remain. No Render management token or additional key is needed in Kaggle.

Use the updated `render_kaggle_client_demo.ipynb`. Its fixed website root is `https://beautycore-demo.onrender.com`; it signs registration metadata with the existing Kaggle backend Secret, verifies acknowledgement and starts a heartbeat. The operational Neon table stores the endpoint/session/lease only, not images or secrets.

After this upgrade, every demo is: **Run Kaggle → wait for CONNECTED TO WEBSITE → open the website**. A lease lasts three minutes and is renewed every minute while the API/tunnel processes and GPU/API ports are alive. If connection fails, the notebook says AI is running but website connection is pending. Do not rerun GPU startup to repair registration.

Fresh automatic Kaggle connection and changed-URL restart acceptance remain Needs verification until live evidence is recorded.

## Every demo: exact operator sequence

1. Open the private tested Kaggle notebook. If the previous session was stopped or failed, start a fresh session. If another AI worker is still active, finish/stop that session before launching a second one. Do not repeatedly run Cell 2 in the same active session.
2. Check Internet, T4 and all three Secrets. Run the three code cells in order. Allow time for dependencies and model loading; no measured startup-time guarantee is available.
3. Wait for **CONNECTED TO WEBSITE** and `READY_FOR_REHEARSAL`. The new URL is registered automatically; no Render setting or deployment is needed each run.
4. If registration is pending, check that the one-time upgrade is deployed and the backend Secret matches. Inspect safe registration messages rather than starting the GPU again.
5. Keep the shared key and the working database/authentication settings in place.
6. For deliberate rollback only, set `AI_ENDPOINT_MODE=static`, update `AI_FASTAPI_URL` and deploy. Automatic mode never silently falls back to an older address.
7. Open the website and refresh it. Sign in using the actual client/demo account.
8. Run the acceptance checklist below before announcing that the demo is ready.
9. Keep the Kaggle GPU session running throughout the appointment. One person generates at a time. Leaving Kaggle open is useful, but the tab alone does not guarantee that its session or tunnel is running.
10. After the demo is finished and no generation is active, stop Kaggle to conserve quota. The website can remain online, but its AI features need the next Kaggle startup.

The client's normal interaction is: open website → sign in → upload photo → request consultation or choose a style → wait for generated result. Starting Kaggle belongs to the operator, not every visitor; Render configuration is one-time in automatic mode.

## Rehearsal before handover

Record which account, notebook version, Render deployment and current URL were used. Verify:

| Check | Success evidence |
| --- | --- |
| Client account access | Notebook can read both private bundles, retrieve enabled Secrets, and obtain the reviewed GPU runtime |
| Kaggle protected readiness | Cell 2 reaches `READY_FOR_REHEARSAL`; this is a prerequisite, not generation acceptance |
| Render authentication | Login succeeds and unauthorized AI access remains rejected |
| Hairstyle | A real suitable portrait produces an image and result controls work |
| Makeup | A real suitable portrait produces an image and result controls work |
| Nails | A suitable hand photo completes a GPU Red/Black look and a renderer Nude/French/Ombre look; visually inspect masking |
| Consultation | Conversation succeeds; all three looks complete sequentially, images display, selection works |
| Switching services | After the previous run finishes, Hair → Makeup → Nails succeeds |
| Overlap/navigation | Document that an accepted job continues and another generation is refused busy; no claim of cancellation |
| Restart | Stop/restart only the demo session, verify automatic registration of the changed URL, create a fresh consultation and generate again without a Render edit/deployment |
| Client device | Repeat login/upload/generation on the actual browser/device used for the defense |

These checks remain **Needs verification** where fresh evidence is absent. Do not replace real-image testing with a health response or the opening Gemini question. Do not stop a live rehearsal session before the final client device test is complete.

## Quick troubleshooting

| Symptom | Operator action |
| --- | --- |
| Website opens, generation fails with 502 | Check Kaggle session/tunnel first, then API/GPU logs; current outage returned tunnel 530 |
| Old tunnel is unavailable | Start the updated tested notebook and wait for automatic connection; static rollback still uses a manual URL |
| Busy/429 | Wait for the existing accepted generation; do not restart the GPU to bypass the lock |
| Old consultation/photo missing after restart | Create a new consultation and upload the photo again |
| Secret startup error | Enable the exact three Secret names and check required minimum lengths privately |
| Environment mismatch | Recover the tested pinned notebook image; do not bypass the original model checks |
| Duplicate startup refused | Do not run another Cell 2 over an active worker; use a fresh session after the old session ends |
| Cell 2 fails | Note the last `DEMO STAGE` and inspect that stage's log in the printed working folder. Do not dump Secret values or the environment |

## What this setup promises

This is a scheduled-demo arrangement with an operator. It does not provide always-on AI. Kaggle resource/session availability, Gemini access, temporary tunnel availability and Render startup are external dependencies. In-memory AI state is temporary. Free compute and a live website do not by themselves guarantee that generation works.

For a permanent unattended client service, replace the operator-dependent GPU/tunnel arrangement deliberately; that is a separate deployment decision.

Maintainer evidence: `docs/experiments/render-kaggle-client-handoff-20261009.json`. Rebuild the starter from its reviewed source with `python scripts/package_render_kaggle_client_notebook.py`; this does not rebuild or replace either private binary archive.
