# BeautyCore generation improvements: local review and GPU benchmark

2026-10-18. Development approved by the Supervisor. **No Render deployment or live database migration has been performed.** Web changes are locally verified; the speed candidate passed the bounded worker comparison and remains disabled pending full application acceptance. This guide concerns the new improvements, not a claim that the currently hosted website already includes them.

## What changed

Generated Hair, Makeup and Nails looks now display a short description and named service estimates. Consultation uses the same information instead of its old demo-only numeric prices and durations. The information also appears in Saved Looks, the look-aware booking form and client/stylist/admin requested-look dialogs.

Prices come from `beautycore/lib/services.ts`. The new style catalog describes the looks and identifies possible services; it does not introduce a second price list. Hair descriptions include new editorial copy. The service options are conditional, not authoritative tariffs for a style: Crew Cut can show Men's Cut, Women's Cut & Blowdry and Children's Cut (under 12) with their existing catalog prices. The client chooses the applicable service; the server calculates the appointment amount from that choice. No photo-based gender/age inference or extra Gemini request is used for this display.

| Service | Existing catalog amount | Display rule |
| --- | --- | --- |
| Men's Cut | PHP 180 | Named booking option |
| Women's Cut & Blowdry | PHP 350 | Named booking option |
| Children's Cut (under 12) | PHP 150 | Applicable only when chosen |
| Blowdry & Style | PHP 250 | Styling option |
| Updo / Special Occasion | PHP 500 | Styling option |
| Bridal Hair | From PHP 1,500 | Keep “From” |
| Classic Manicure / Gel Manicure | PHP 180 / PHP 350 | Separate named options |
| Nail Art (per nail) | From PHP 50 per nail | Keep unit; do not multiply or assume add-on rules |
| Makeup Application | Price to be confirmed | No invented amount |
| Perm Curls / Wavy | Price to be confirmed | No matching priced service is established |

New saves capture the description, estimate options and catalog version/time in a nullable `look_details` JSONB field on the existing generation. No second image is stored. Duplicate saves/restores preserve the original snapshot; a price change does not rewrite it. Booking displays the snapshot as “Estimated cost when saved” and separately uses today's selected service amount. Older records have no historical snapshot and show a clearly labeled current estimate. Requested-look access continues to use the existing owner/assigned-stylist/admin permissions.

The public Hair save catalog/checker now covers the thirteen approved hosted styles, including the additional adapter's Bun. This corrects saves rejected by the previous three-style snapshot; it does not enable new model styles.

Market Trends is removed from the active admin route and sidebar. Its old URL receives the normal missing-page response. Shared statistics, generation history, Finance, Dashboard and database records remain. Archived `_legacy_src` files are unchanged.

## Safe local review

The additive migration is `beautycore/db/migrations/0004_look_details.sql`. It preserves the old ten-argument save function and creates a distinct snapshot-aware function. The application must receive this migration before a future deployment. It has only been run against isolated test databases during this task.

For local fixture verification, run from `beautycore`:

```powershell
npm run test:business
```

This uses disposable PGlite and DOM fixtures, not the configured Neon database. Do not run a migration apply command, `db:push` or `db:seed` against the production connection for this review. The existing local environment points to shared services, so running the app without an isolated, migrated development database is not a safe substitute for the fixture tests.

Review these flows with an isolated development database when doing device acceptance:

1. Open completed standalone Hair, Makeup and Nails results. Check description and named estimates. Repeat in Consultation, including its selected summary. Check fixed, starting-from, per-nail and quote-required cases.
2. Save a completed result, reload Saved Looks, open Book and choose an applicable service. Verify the saved estimate remains visible and the appointment uses the selected service's current amount.
3. With synthetic data, change a catalog price after a save. The old snapshot must retain its amount; the new booking must use today's catalog amount. Duplicate save and restore must retain the snapshot. Old rows must show the current-estimate label.
4. Assign the booking to a stylist. That stylist and an admin must see the same booked image and description; another stylist/account must be denied. Gallery removal must not remove the booked reference.
5. Open admin Finance and Dashboard, including completed-service daily reporting. Market Trends must be absent from navigation and its old URL must be missing. Existing history must remain.

Automated component tests exercise these flows, but they do not establish real phone layout, live browser acceptance, Neon capacity or real generated-image sizes. Those remain review gates.

## Why the speed change is not enabled yet

Historical evidence and source show five sequential model calls for a five-nail Red/Black hand and three sequential looks for Consultation. Hosted Nails already uses eight inference steps; reducing twenty to eight is not a new optimization from this task. Hair/Makeup remain twenty steps. The hosted CPU facade calls its GPU worker over localhost, so five nail crops are not five separate internet round trips.

The fixed positive and empty negative prompts are encoded again for each model call. The candidate reuses only those public prompt tensors. It keeps a bounded CPU cache (four entries, at most 64 MiB), keys model/adapter/prompt/encoder/device options and clears on failure. Portraits, image latents and generated results are not cached. Existing masks, adapters, model revision, seed, steps, resolution, worker serialization and busy/cancellation rules remain.

The optional worker flags are `AI_INFERENCE_PROFILE=1` for diagnostic phase timings and `AI_PROMPT_CACHE=1` for the candidate cache. **Leave both unset in the working demo.** No flag has been set in Render/Kaggle. Profiling adds synchronization overhead; the paired speed samples disable phase barriers and collect a separate diagnostic warm-up. Persistent CPU segmentation is not implemented because its contribution still needs current measurements.

CPU tensor tests prove repeated encoding work can be reused in the wrapper. The subsequently returned GPU artifact now also verifies identical outputs and bounded repeated-use timing gains; see the review below. Full application latency and general image quality remain separate gates.

## Run the separate private Kaggle comparison

The Supervisor confirmed a separate benchmark session is available. Use it rather than replacing the working demo notebook.

1. Locate `notebooks/beautycore_generation_speed_benchmark.ipynb` in this checkout. In Kaggle create a **new private notebook** and use its notebook import/upload action to import that file. Keep the existing Render demo notebook unchanged.
2. Select the **T4 GPU** accelerator and enable Internet. Attach the existing private dataset containing exactly one `capstone_train002_20260928_v1.bin`. The expected bundle SHA-256 is `f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac`. This notebook does not need the CPU demo bundle or any API Secrets.
3. Run the single code cell once. It creates its own `beautycore-speed-<random>` folder under `/kaggle/working`, verifies the immutable private bundle and source overlay, checks the reviewed Python/Torch/CUDA/T4 environment, installs the pinned runtime and downloads the pinned foundation. It loads the model directly: no HTTP server, tunnel, endpoint registration or Render configuration change.
4. Allow setup and the paired runs to finish. This consumes GPU quota and can take tens of minutes. The original long inference workloads are deliberately retained for an honest comparison. Do not run competing inference in the same benchmark session.
5. At `DOWNLOAD_RESULTS`, open the printed folder in Kaggle Output and download `beautycore-speed-results.zip`. It contains `results/report.json` and the baseline/candidate images. Keep the notebook, dataset and resulting comparison images private because the approved input portraits are included in the generated outputs.
6. Return that ZIP/report and comparison outputs for review. Do not enable the candidate in the working system just because the notebook finishes.

The notebook uses the same approved image, adapter, seed 1977, guidance 4, 512-pixel input and inference steps in both modes. Crew Cut, Natural Makeup and Classic Red receive three paired timing runs each; Bun and Glossy Black receive one pair for adapter coverage. Run order alternates. The first candidate run has a cold prompt cache; later runs reuse it. The report includes sample counts, medians/ranges, pixel hashes, cache counts and peak allocated GPU memory. It reports a slower candidate honestly and makes no percentile claim from three samples.

**Scope:** Nails here is the approved single localized crop. The notebook does not measure a complete five-nail hand, CPU localization/refinement, Render/browser/network time, renderer styles or all three Consultation results. After reviewing the worker comparison, a separately approved candidate application rehearsal must compare full-hand masks/composites, all expected nails, Hair/Makeup identity, Hair adapter restoration, renderer styles and time to first/all Consultation results. No end-to-end speed or quality signoff is implied by this worker test.

If setup stops, retain the printed workspace and `setup-evidence` logs. A host mismatch is an explicit compatibility stop, not permission to unpin dependencies, lower quality settings or edit the working demo. Report the non-secret `host.json` and error. If inference fails, `results/report.json` records the failure and existing partial outputs are preserved; the final ZIP is produced only after a successful benchmark process.

## Verified and still pending

Web AI routing/business regressions, Python backend/worker tests, disposable migration/idempotency checks, source catalog synchronization and the production build were run locally. Exact outcomes are recorded in `docs/experiments/generation-improvements-development-20261018.json`.

The new GPU worker report and exact-output comparison have now been reviewed: Crew Cut65.005→56.642s, Natural Makeup65.653→56.431s and single-nail Red37.475→29.055s medians (three pairs each). All eleven baseline/candidate pairs are byte/pixel identical. Gains depend on reused prompts; Bun/Black have single cold pairs only. [Full interpretation](../experiments/generation-speed-benchmark-20261018-review.md). Still pending: full-hand/application/device acceptance, confirmed Makeup/missing service prices and special Nail Art pricing rules. Native mobile's strict Consultation contract still carries its existing demo numeric fields; this web slice preserves that contract and does not claim native price consistency. No code was pushed, no old demo bundle was rebuilt, and no live migration, notebook replacement or Render deployment was performed.

## Completed worker benchmark — no rerun needed for this review

The user supplied `beautycore-speed-results.zip`; independent CRC, inventory, timing-summary and all22 image-hash checks passed. The separate experiment record preserves the raw report. The dominant measured worker phase remains the model image-generation loop (about73–85% in diagnostic warm-ups). The candidate improves repeated-prompt worker cases while preserving their exact outputs; first-use performance is not consistently faster. It remains disabled in the working system pending the narrower full application rehearsal. No further27-generation benchmark is required merely to confirm this artifact.
