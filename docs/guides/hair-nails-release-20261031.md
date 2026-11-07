# Approved French Bob + Nails release

Date: 31 October 2026  
Release: styles-20261031-01  
Status: **Prepared locally; fresh Kaggle and website rehearsal required**

## What this release adds

The Supervisor approved French Bob after it was identified as the sole Hair candidate recommended for review. This approval covers the actual curly interpretation shown in HAIR-EXP-002. The description states that the preview may change hair color. It does not establish a fix for color preservation.

This release contains:

- Textured French Bob with Wispy Bangs: exp_french_bob_wispy.
- Raspberry Jelly: exp_raspberry_jelly.
- Pink Aura Ombré: exp_pink_aura.
- Negative-Space Micro-Dots: exp_negative_space_microdots.

Butterfly, Wolf, Two-Block and Comma stay held. Makeup additions and the original white-cast correction remain unresolved. Current local business metadata contains14Hair,10Makeup and8Nails, totaling32styles. The new pinned expanded notebook is expected to expose that catalog; a legacy fallback exposes its own smaller supported catalog.

## How French Bob works

French Bob uses exactly the reviewed candidate prompt with the original verified TRAIN-001 adapter. It uses guidance4.0,20steps,seed1977,512x512 and full adapter influence. No checkpoint or training metadata is rewritten. It is an additional inference profile using an existing trained adapter; it was not added to the checkpoint's historical training-label claims.

The shared worker verifies original checkpoint ownership before loading. A separate release extension supplies the additional public routing/profile and reports its loaded capability. The facade checks its exact release/profile evidence, then verifies the output's style ID, adapter/checkpoint, profile/prompt hashes, settings, dimensions and truthful trained_style:false metadata. Baseline Hair methods and the original worker source remain preserved. Only the fresh extracted release workspace receives the verified extension.

One foundation and the existing serialized adapter switching remain. The previous Nails-only public-prompt optimization is retained; no new Hair caching or faster generation guarantee is introduced.

Descriptions and estimates use existing salon services: Men's Cut PHP180 and Women's Cut & Blowdry PHP350. These are existing service options, not a new fixed French Bob price. The client chooses the appropriate service; the salon confirms applicability/final price. Existing Nail service estimates and per-nail qualifiers remain unchanged.

## Files

Paths are relative to I:\HAIR on this computer.

| Item | File |
|---|---|
| New starter | notebooks/render_kaggle_hair_nails_demo.ipynb |
| New CPU input | artifacts/render_kaggle_cpu_hair_nails_20261031_01.bin |
| Existing GPU input, unchanged | artifacts/capstone_train002_20260928_v1.bin |
| Release inventory and hashes | docs/experiments/hair-nails-package-20261031.json |
| French Bob approval | docs/experiments/french-bob-approval-20261031.json |

Use this combined starter for the new release. Do not mix its CPU input with the old starter or attach duplicate copies of either required input.

The earlier original/optimized notebooks, Nail-only notebook, original CPU input and Nail-only CPU input are preserved. The matching Render code explicitly recognizes both the current release and the exact preserved Nail-only release. Legacy facades without new release evidence retain their original catalog behavior. A French-enabled facade refuses a legacy worker that lacks the new Hair profile.

## Release order

This preparation does not commit/push source, deploy Render, start Kaggle or change a production database.

1. Publish the reviewed matching application source to the confirmed deployment branch.
2. In the existing Render service, deploy that matching revision. Keep beautycore as root, existing build/start commands and existing secrets/settings.
3. Preserve the currently working Kaggle notebook and finish accepted jobs before switching.
4. During a planned interruption, start the new notebook with the new CPU input and original GPU input.
5. Complete the website checklist below before giving the new starter to the client.

Do not start this notebook against an unverified older Render revision. Deploying only the website does not update Kaggle's Hair support.

No database migration or new credentials are required. Keep AI_ENDPOINT_MODE=registered. No routine AI_FASTAPI_URL editing is needed.

## Kaggle steps

1. Make a separate private copy of the tested pinned Kaggle notebook. Preserve the reviewed image and old notebook.
2. Import render_kaggle_hair_nails_demo.ipynb. Use a unique notebook title.
3. Upload render_kaggle_cpu_hair_nails_20261031_01.bin as a new dataset/input and grant the client's account access when needed.
4. Attach the existing input containing capstone_train002_20260928_v1.bin.
5. Attach exactly one copy of the new CPU input. Remove duplicate/unrelated attachments from this new notebook only; do not delete the original datasets.
6. Select the reviewed T4 configuration and enable Internet.
7. Enable the existing AI_BACKEND_API_KEY, AI_REMOTE_API_KEY and GEMINI_API_KEY Secrets. The backend key must match Render. Do not paste values in notebook cells or messages.
8. Stop the prior AI session when ready to switch. Run the new notebook's three code cells once, in order.
9. Wait for CONNECTED TO WEBSITE, then keep the Kaggle session running.

Cell1 verifies original archive/member hashes, the CPU/GPU release pair, profile hashes and matching worker-source inventory. Cell2 prepares isolated environments, starts the authenticated shared worker/facade, verifies readiness and registers automatically. Cell3 reports the release.

If an old heartbeat is active, registration can refuse takeover. After stopping it, allow its180second lease to expire; do not edit lease records. If host/package/model guards fail, preserve logs and investigate instead of bypassing them.

## Website rehearsal

Submit one generation at a time using a test account.

1. Confirm French Bob appears in Hair Studio with the correct name and hair-color limitation.
2. Generate it on each of the two HAIR-EXP-002 source photos, using the original fixtures preserved in the result ZIP. Check the requested style, face/fringe, source framing and color limitation. Compare decoded output pixels to cases6and8 where the same pinned environment/settings are used; investigate any unexpected difference.
3. Check a second ordinary portrait manually. Prior two-source acceptance does not establish all-user fidelity.
4. Confirm the other four held Hair IDs remain unavailable.
5. Generate an existing Hair style, baseline Makeup, model Nails Red/Black and each new Nail renderer. Verify switching/restoration and existing model settings.
6. Run a Hair consultation and generate French Bob when selected/recommended. Recommendations need not always include it.
7. Save the result, reload Saved Looks and verify its image, description and captured service estimate.
8. Book the saved result with an eligible stylist and appropriate existing service. Verify the actual service price and same image/details on client and assigned-stylist dashboards. Another stylist must not see that private image.
9. Exercise the existing completion/review/admin workflow and guest trial limit.
10. Stop Kaggle after preserving the saved look. Confirm stored/booked images remain accessible, then restart in a fresh session and verify automatic registration.

Local synthetic tests and real checkpoint/archive validation do not replace this GPU/browser rehearsal. The approved offline output quality is evidence for one profile, not proof of live deployment.

## Fallback

Stop the failing new session, preserve logs and allow its registration lease to expire. Start the preserved working optimized notebook with its original inputs, or the preserved Nail-only notebook with its matching Nail-only CPU input.

Keep the compatible new Render application so new French Bob/Nail snapshots remain readable. A fallback runtime cannot generate a style absent from its actual catalog; existing saved images/bookings remain. Do not delete database records to roll back generation.

## Developer checks

~~~text
python scripts/generate_style_release.py
python scripts/check_saved_look_catalog.py
python -m scripts.package_hair_nails_release
~~~

The builder produces separately named immutable artifacts and refuses to replace differing bytes under the same name. The original GPU archive, exact training metadata, frozen registries and previous release artifacts are retained.
