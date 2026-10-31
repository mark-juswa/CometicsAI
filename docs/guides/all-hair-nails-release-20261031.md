# Deploy five approved Hair styles and three Nail designs

Date: 31 October 2026
Release: styles-20261031-02
Status: prepared; Render rollout and a fresh Kaggle/website rehearsal are required.

## Scope

Add Butterfly Cut, Wolf Cut, Korean Two-Block, Korean Comma Hair and Textured French Bob with Wispy Bangs. Use the exact five reviewed HAIR-EXP-002 prompts, original TRAIN-001/TRAIN-002 checkpoints, full adapter weight, guidance4.0, 20steps, seed1977 and512square. These are additional inference profiles, not newly trained labels/checkpoints.

Add Raspberry Jelly, Pink Aura Ombré and Negative-Space Micro-Dots using the three already reviewed renderers. Retain the existing Nails-only prompt cache and existing inference settings.

Keep all original Hair/Nail styles. Keep the existing ten Makeup presets/model/settings; no new Makeup style or attempted whitening fix is released. Pearl Chrome and Cat-Eye remain unbuilt and disabled.

Descriptions state the reviewed Hair limitations honestly: Butterfly may be bob-like, Wolf can be spiky, Two-Block/Comma can cover eyes, French Bob can be curly, and Hair previews may recolor hair. Salon services/prices remain existing options, not invented new style prices. Local metadata totals18Hair/10Makeup/8Nails=36styles.

## Files

- New starter: notebooks/render_kaggle_all_hair_nails_demo.ipynb.
- New CPU input: artifacts/render_kaggle_cpu_hair_nails_20261031_02.bin.
- Existing GPU input: artifacts/capstone_train002_20260928_v1.bin, unchanged.
- Exact hashes/inventory: docs/experiments/all-hair-nails-package-20261031.json.

Do not use the earlier French-only or Nail-only starter with this new CPU input. Previous starters, inputs and exact compatible manifests remain preserved for fallback.

## Render — do this first

1. Deploy the published release commit from codex/render-kaggle-demo in the existing beautycore-demo service.
2. Keep beautycore as the root directory. Keep existing build/start commands, environment values and secrets.
3. Wait for that commit's deployment to become Live. Check /api/health returns status ok.
4. No database migration, new secret, training or routine AI_FASTAPI_URL change is required. Keep AI_ENDPOINT_MODE=registered.

Publishing to GitHub does not mean Render is deployed; automatic deployment is disabled in render.yaml. This session has no supported Render control connection/API credential, so the operator must start Manual Deploy.

## Kaggle — once matching Render is Live

1. Preserve the old working notebook. Make a separate private copy of the previously tested pinned Kaggle notebook so the known environment remains.
2. Import render_kaggle_all_hair_nails_demo.ipynb into that new copy. Give it a unique title.
3. Upload render_kaggle_cpu_hair_nails_20261031_02.bin as a new dataset/input.
4. Attach exactly one input containing capstone_train002_20260928_v1.bin and exactly one input containing the new CPU filename. Remove duplicate/old CPU attachments from the new notebook only; do not delete old datasets.
5. Select the reviewed T4 configuration and enable Internet.
6. Enable existing AI_BACKEND_API_KEY, AI_REMOTE_API_KEY and GEMINI_API_KEY in Kaggle Secrets. The backend key must still match Render. Never put secret values in cells.
7. Stop any prior serving session only when ready to switch. Run all three new code cells once, in order.
8. Wait for CONNECTED TO WEBSITE. Cell3 should show release styles-20261031-02 and eight additions.
9. Keep that Kaggle session running while using the website. A stopped session cannot serve AI requests.

Registration updates the endpoint automatically. If another session's heartbeat lease is active, stop that old session and allow up to180seconds for expiry; do not edit Render's endpoint or database records to force takeover.

If startup fails, keep the exact stage/log/error. Do not rerun extraction over a running service, remove integrity assertions, relax model pins, or mix bundles. No new GPU service was started by local preparation.

## Website rehearsal

1. Log in using an existing client account.
2. Confirm Hair lists the five additions and Nails lists the three additions. Confirm no new Makeup styles.
3. Generate one Hair output using TRAIN-001 (French or Butterfly), then one using TRAIN-002 (Wolf/Two-Block/Comma). Compare against the approved appearance and stated limits.
4. Generate one added Nail design on a clear hand photo. Repeat for the other two designs before handing over.
5. Complete a Hair/Nail consultation. Verify recommendations refer only to available styles and generate the selected output.
6. Save one generated Hair look and one Nail look. Refresh Saved Looks.
7. Book a saved look with the matching service/stylist. Confirm image, description, real service estimate and selected stylist on the client and assigned stylist dashboards.
8. Confirm guest trial still permits only its existing allowance. Avoid running multiple generations together; the single shared GPU serializes work.
9. Verify a baseline Hair style and existing Makeup request still work. Makeup retains its known white-cast limitation; it is not claimed fixed.
10. Record each result. CONNECTED TO WEBSITE proves registration, not all-feature visual/generation/save/book acceptance.

## Fallback

Render explicitly recognizes exact current and preserved French-only/Nail-only release evidence, plus the existing baseline facade behavior. Stop the new session before starting an old fallback notebook with its own matching original inputs. Wait for the lease to expire, then let automatic registration reconnect. The old facade serves its own smaller catalog.

Do not delete saved looks or appointments. The new application retains existing/new business metadata so saved information remains accessible even if the active AI fallback supports fewer generation styles.
