# Approved Nail expansion: release and client handoff

Date: 30 October 2026  
Status: **PREPARED locally; cloud rehearsal and rollout NOT STARTED**

## What is included

The Supervisor approved the repaired four-hand gallery with: "I approve the design it looks good."

This release adds only these reviewed designs:

| Design | Stable style ID | Processing |
|---|---|---|
| Raspberry Jelly | exp_raspberry_jelly | CPU nail rendering and existing original-photo compositing |
| Pink Aura Ombré | exp_pink_aura | CPU nail rendering and existing original-photo compositing |
| Negative-Space Micro-Dots | exp_negative_space_microdots | CPU nail rendering and existing original-photo compositing |

The existing five Nail styles remain, giving eight Nail options in this release. The expanded TRAIN-002 notebook retains its thirteen Hair and ten Makeup options: 31 catalog entries in total. This count is not a live website verification.

New Nail results identify their renderer profile and do not claim to use a trained image-generation adapter. The segmentation/localization components still use the existing learned models. New designs make no diffusion-model request.

Descriptions and service estimates use the existing salon catalog: Classic Manicure PHP180, Gel Manicure PHP350, and Nail Art from PHP50 per nail. These are service choices, not a guaranteed total or a new design surcharge. The salon confirms whether extra nail-art charges apply.

Hair/Makeup expansion and the remaining two Nail finishes are not enabled. The original Makeup white-cast limitation remains; rejected experiments are not included. No new model training, pricing invention, provider, database migration or per-session Render setting is required.

## Files to use

Paths below are relative to the repository root. On this computer the root is I:\HAIR.

| Item | File |
|---|---|
| New starter | notebooks/render_kaggle_expanded_nails_demo.ipynb |
| New CPU input, about 27.9 MB | artifacts/render_kaggle_cpu_styles_20261030_01.bin |
| Existing GPU input, unchanged | artifacts/capstone_train002_20260928_v1.bin |
| Exact hashes/source inventory | docs/experiments/expanded-nails-package-20261030.json |
| Human approval record | docs/experiments/expanded-nails-approval-20261030.json |

The original render_kaggle_optimized_demo.ipynb, render_kaggle_client_demo.ipynb and render_kaggle_cpu_20261009.bin are preserved as fallback. Do not edit or replace their datasets.

The new starter includes the existing Nails-only public-prompt cache. Model weights, adapter ownership, seeds, guidance, inference steps, output dimensions and Hair/Makeup settings remain unchanged. No additional speed gain is claimed from this catalog release.

## Release order

The package is ready for a controlled rehearsal, not yet a completed deployment.

1. Publish the reviewed application release source to the confirmed deployment branch. This preparation did not commit or push it.
2. In the existing Render service, deploy that matching revision. Keep the existing repository, beautycore root, build/start commands, secrets and registered endpoint mode. Do not use Deploy latest commit while GitHub still contains only the previous release.
3. Keep the current Kaggle notebook running until a planned interruption. Finish accepted jobs and save any needed previews first.
4. Start the new Kaggle notebook during that gap, following the next section.
5. Run the full website checklist below. Connected status alone is not proof that the release works.

Deploying Render alone cannot update the Kaggle catalog. Starting the new notebook against an incompatible Render revision can reject registration.

The new Render code permits the working legacy Kaggle facade without new release fields. A new facade must report the exact matching release digest and installed style capabilities. Signed registration, heartbeat, active-session checks and lease behavior stay unchanged.

## Kaggle setup, once for this release

1. Make a private copy of the tested notebook with its reviewed Kaggle image pinned. Preserve the old notebook separately.
2. Import render_kaggle_expanded_nails_demo.ipynb into the copy. Give it a unique title.
3. Upload the new render_kaggle_cpu_styles_20261030_01.bin as a new dataset/input. Share access with the client's account when needed. Retain the exact filename.
4. Attach the existing GPU input containing capstone_train002_20260928_v1.bin.
5. Attach the new CPU input. For clarity, remove the old CPU input and unrelated duplicate datasets from this new notebook only. Do not delete the source datasets. There must be exactly one match for each required filename under /kaggle/input.
6. Select the reviewed T4 GPU configuration and enable Internet. If the client account has no suitable GPU access, this setup cannot provide online inference.
7. Enable these existing Kaggle Secrets: AI_BACKEND_API_KEY, AI_REMOTE_API_KEY and GEMINI_API_KEY. The backend key must match Render. Never paste key values into code, chat or shared output.
8. Stop the old AI session only when ready to switch. Do not start two workers for the same website.
9. Run the three code cells once, in order.

Cell 1 verifies archive/member hashes, the original host/model contract, the CPU/GPU release pair and the optimization payload. It extracts into a fresh unique workspace.

Cell 2 prepares the isolated CPU environments, starts one shared GPU worker and the authenticated facade, checks the loaded Nail release and automatically registers its tunnel with the existing website.

Cell 3 reports the session. Wait for CONNECTED TO WEBSITE, then keep the Kaggle session running.

A former active heartbeat can refuse takeover. After stopping it, allow its 180-second lease to expire; do not alter database lease records. A host/package mismatch must be investigated, not bypassed.

The client needs a browser, their enabled Kaggle GPU account, dataset access and Secrets. No local Python or GPU installation is needed. Later scheduled starts use this same notebook and inputs; no routine Render URL editing.

## Website rehearsal

Use a test account and eligible stylist. Submit one generation at a time.

1. Open Nail Studio. Confirm all five old styles plus the three additions appear with the correct names.
2. Upload an appropriate hand photo. Generate each new design. Confirm the requested result, clear edges, original skin/background preservation and no unexplained failure.
3. Read each description and service estimate. Confirm the per-nail price qualifier and absence of an invented fixed design total.
4. Start a Nails consultation. Confirm recommendations use supported catalog IDs and can generate an added design when selected/recommended. The three suggestions need not all be new styles.
5. Save one added design. Reload Saved Looks and verify the same image and captured description/estimate.
6. Book that saved look with an eligible stylist and the appropriate manicure service. Confirm the appointment price comes from the selected service.
7. Open the client and assigned-stylist dashboards. Check they show the same booked image/details. A different stylist must not access the private image.
8. Complete the appointment and review it using existing rules. Confirm admin monitoring continues to work.
9. Generate one old Hair look, baseline Makeup, model Nails Red/Black and an old renderer Nail style. Hair/Makeup generation settings must remain baseline. Record the known Makeup appearance limitation separately.
10. Check a guest trial still enforces its existing one-image limit.
11. Preserve the saved look, stop Kaggle and confirm the durable saved/booked image is still available. Restart the same new notebook in a fresh session and verify automatic reconnection without editing Render.

Record actual timings and failures; no new GPU/browser rehearsal has run during local preparation.

## Fallback

If the new runtime fails:

1. Preserve the failed notebook logs/results.
2. Stop that session and let its registration lease expire.
3. Start the preserved working optimized notebook with its original GPU and CPU inputs and existing Secrets.
4. Keep the compatible new Render application so new saved-look metadata remains readable.

The new designs will not generate on the old Kaggle catalog, but already saved images and booking snapshots remain. Do not delete saved looks, bookings or database columns to roll back generation.

## Developer verification

From the repository root:

~~~text
python scripts/generate_style_release.py
python scripts/check_saved_look_catalog.py
python -m scripts.package_expanded_nails_release
~~~

The builder is immutable and deterministic: rerunning identical source succeeds; changing a published artifact under the same filename fails. Use a new version when release source changes.

Relevant automated checks cover actual FastAPI renderer dispatch, consultation catalog classification, original-mask compositing, exact reproduction of twelve historical outputs, archive roundtrip/tampering, matching notebook payload, existing optimization, metadata persistence, real disposable-database booking and role-based image access. These do not replace the operator's live Kaggle/browser rehearsal.
