# Private full-hand and consultation generation rehearsal

2026-10-18. Supervisor approved the next isolated rehearsal with “proceed” after the completed worker comparison. **This is a test notebook, not a replacement server. No Render deployment or live database change is included.**

## Exact steps

1. Use `I:/HAIR/artifacts/application-rehearsal-20261018/beautycore_application_rehearsal.ipynb`. This generated file is private and deliberately ignored by Git because it includes one approved original hand from the earlier 11K Hands evaluation. It contains no model weights, customer photo or API keys.
2. Create a **separate private Kaggle notebook** and import that `.ipynb`. Keep the working Render demo notebook unchanged. Select **T4 GPU** and enable **Internet**.
3. Attach both existing private inputs: the dataset with `capstone_train002_20260928_v1.bin` and the dataset with `render_kaggle_cpu_20261009.bin`. Attach exactly one copy of each file. No new dataset, secret or Render URL is required.
4. Run the single code cell **once**. Allow tens of minutes: it performs20 application results and30 model calls. Each Red/Black full-hand result requires five calls. Progress shows `REHEARSAL START`, updates roughly every15seconds during generation, completed worker-call counts and `REHEARSAL DONE`. Setup has separate stage messages. Do not rerun the cell while it is working.
5. When `DOWNLOAD_REHEARSAL_RESULTS` appears, download `beautycore-application-results.zip` from the printed `/kaggle/working/beautycore-app-check-<random>/` folder. Return it for timing/full-hand visual review. A partial ZIP is also written when setup/inference fails; retain that evidence rather than rerunning blindly.

Keep the notebook and output ZIP private. The run stops its own temporary GPU worker afterward, so it does not provide a URL to paste into Render. It never opens a public tunnel, registers an endpoint or modifies an existing demo worker.

## What it runs

The baseline and candidate each run the same sequence:

| Sequence | Actual implementation exercised | Model calls per mode |
| --- | --- | ---: |
| Hair Consultation: Bob Hair, Bun, Crew Cut | Existing deterministic recommendations, private photo/session, three real sequential generations, result retrieval and selection; TRAIN-001 → TRAIN-002 → TRAIN-001 | 3 |
| Natural Makeup | Actual central feature route and remote validator | 1 |
| Crew Cut again | Hair restoration after Makeup; compare pixels with the earlier Crew result | 1 |
| Nails Consultation: Classic Red, French Tip, Glossy Black | Real1600×1200 hand, MediaPipe, coarse YOLO, original-resolution fingertip refinement, per-nail model crops or renderer, final compositor, async result retrieval and selection | 10 |
| Nude Pink, Pink Ombre | Remaining deterministic renderer branches, same full hand and preservation checks | 0 |
| **Per mode / both modes** | **10/20 application results** | **15/30** |

The private hand is the previously reviewed identity0000045, SHA-256 `c483244132e74ffc6e492271e742c17dce4ce694050abab78c43bc306dd4fd98`. It is an approved dataset fixture, not a client's upload or a new training sample. Generation parameters remain fixed: existing foundation/adapters, seed1977, guidance4, Hair/Makeup20steps, model Nails8steps. The test does not retrain anything.

This notebook runs the existing authenticated async facade and CPU API through an in-process ASGI client, with **real loopback HTTP** from the CPU API to one GPU worker at127.0.0.1:8765. CPU dependencies and segmentation Torch run in their own fresh environments; the known Kaggle ensurepip and Matplotlib-inline failures are handled with `venv --without-pip`/isolated pip installation and `MPLBACKEND=Agg`. The exact reviewed GPU runtime is checked before use. A host mismatch stops rather than changing the accepted settings.

Only the separate test worker has an authenticated mode-control route. It refuses invalid inputs and changes while GPU work is owned. It creates a fresh baseline/candidate profiler/cache without altering the production worker module or default flags. These test routes are not added to any demo packaging inventory.

## What the evidence checks

- Every generation is admitted as an async job and polled to completion. Missing authentication is rejected; another owner cannot read the job; a competing submission returns429 while admitted work continues. No automatic inference retry is used.
- Real Consultation state is created, receives its photo, produces exactly three expected catalog recommendations, generates them sequentially, returns completed detail and permits selecting a completed result. The provider is the **existing deterministic provider** so both sides use identical recommendations. No Gemini call or conversation-latency claim is made.
- Every full-hand result must report all five nails. An observer copies the actual refined mask/finger masks without changing the pipeline's returned objects, thresholds, crops or material proposal. Every expected finger must have changed pixels; all pixels outside the actual final mask must remain unchanged.
- Worker audit counts must match five calls for Red/Black, one for Hair/Makeup and zero for renderer styles. A single loaded foundation must remain ready. Worker audit/provenance, model/environment setup evidence and source overlay hashes are included in the ZIP.
- Ten baseline/candidate pairs are compared by decoded RGB and final-mask hashes. The report also records PNG byte hashes and full-hand PNG/mask files. Any output/mask difference fails the comparison and retains evidence for review. Hair restoration is separately checked within each mode.
- The report includes each request's wall time, CPU phase metadata, worker cache counters, and sequence time to first/all Consultation results. Timed request completion includes the two-second local polling interval. Consultation sequence times also include local result checks between generations.

## Limits and next decision

One paired application observation per case is sufficient for a focused regression comparison, not a latency distribution or universal speed percentage. Baseline runs first and its initial request may include kernel/adapter warm-up; interpret its timings alongside the already completed three-pair worker benchmark. The script does not add another warm-up benchmark just to repeat prior evidence.

The whole hand is now exercised, but only one approved hand is included. Full-hand finish, skin boundaries, all five nails and identity/style appearance still need inspection of returned images. Exact pixel equality preserves the baseline; it does not prove baseline aesthetics are ideal.

This is **not** a Next.js/browser, live Render, client-device, saved-look/booking database, Gemini conversation or three-look Makeup Consultation acceptance test. Those components were not changed by this cache experiment; their separate requirements and current verification limits remain. No native application update is included.

The candidate remains disabled in the working demo until the returned evidence is reviewed. The earlier instruction **do not deploy to Render** remains in force. No new live schema migration, model bundle rebuild or cloud configuration change is performed by this notebook.

Local checks use synthetic vision/GPU boundaries around the real gateway/Consultation router. They verify the test harness, not real Kaggle model performance. See `docs/experiments/application-rehearsal-preparation-20261018.json` for exact local test and generated-artifact evidence.
