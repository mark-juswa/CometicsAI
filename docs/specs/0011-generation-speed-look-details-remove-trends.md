# Generation performance, look information and Market Trends removal

**2026-10-18 (Asia/Manila). Decision: CONFIRMED by Supervisor “lets start”. Inspection: DONE / source and existing evidence VERIFIED. Web implementation: DONE / local regression VERIFIED. Performance candidate: bounded GPU worker comparison VERIFIED / full application adoption NEEDS VERIFICATION.**

Inspected checkout: `I:\HAIR`, commit `6bd961e` on `codex/saved-looks-bookings`. The environment's `F:\HAIR` location is stale. The initial audit below describes the pre-change checkout. Development now lives on local branch `codex/look-details-performance`; the implementation adds web look metadata, an unapplied additive migration and a separate private benchmark. Existing model weights, demo bundles/notebooks, live database and Render deployment/configuration remain unchanged. The Supervisor explicitly says **do not deploy this update to Render**. Earlier authorization for the previous saved-look release does not authorize deploying these new improvements. The previous database migration is verified; its Render activation is not independently confirmed in this audit.

## 1. Actual pipeline and performance findings

Current hosted source routes BeautyCore web requests through the authenticated Next.js AI adapter to a Cloudflare tunnel, the private Kaggle CPU facade/FastAPI, and a **loopback** unified GPU worker (`http://127.0.0.1:8765`). Individual nail crops do not traverse Render/Cloudflare again in that hosted topology. Do not blame five internet round trips without evidence.

| Component | Verified behavior | Performance implication |
| --- | --- | --- |
| Shared GPU | `scripts/unified_gate3_server.py` loads one pinned FLUX.2 Klein Base, FP16, model CPU offload; `SharedExperiment` owns one serialized worker. | Base loading is startup work, not repeated for every image. CPU/GPU movement trades speed for memory, but its current share needs measurement. |
| Hair/Makeup | Original runtime methods run one full 512×512 pipeline call, 20 steps, guidance 4 and seed 1977. | Model work, prompt encoding and image encoding/decoding are inside the generation call. Existing total timers do not isolate these subphases. |
| Nails Red/Black | `HybridNailsPipeline.run` loops through localized nails and awaits a separate full model call for each crop. | A five-nail hand incurs five sequential model calls. This is the strongest measured bottleneck in existing evidence. Do not parallelize the one-owner worker or skip nails to hide it. |
| Renderer Nails | Nude Pink, French Tip and Pink Ombre retain localization/segmentation/refinement/compositing but bypass FLUX. | A measured renderer result took 12.531 s while reported style-rendering/compositing was about 0.031 s; detector/geometry/other request work dominates that example, not rendering itself. |
| Segmentation | `IsolatedYoloNailSegmenter` starts separate Python subprocesses for coarse and refined segmentation. `nails_segment_once.py` loads YOLO per invocation; the refinement invocation handles all fingertip ROIs. | Repeated process/import/model-load overhead is a candidate to measure. It is not one new model load per refined fingertip. |
| Consultation | Web `generatePending` explicitly awaits three recommendations one at a time through the same generators. | Time to all three looks approximately adds their individual request times; first-completed-result time is a different metric. Conversation/Gemini time must be measured separately. |
| Hosted admission | `demo_gateway.py` has one busy generation slot, rejects competing submissions with 429, and returns job tickets. | There is no unbounded hosted generation queue to optimize. The GPU ownership lock also serializes work and protects adapter state. Leaving a page need not cancel admitted work. |
| Browser | `browser-client.ts` polls accepted jobs every two seconds. | Polling can add result-detection delay and HTTP overhead; shortening it does not make minute-long model inference faster. |
| Adapter switching | Same verified adapter is reused; changing adapters unloads/reloads and rechecks provenance. | Historical Gate 2 transition samples are roughly 0.77–2.58 s, well below the measured full model calls. Re-loading the foundation every request is not the observed design. |

### Measured evidence already in the repository

These are **historical observations**, not a fresh benchmark of today's client/session or a new improvement from this task.

| Evidence | Observed time | Scope/limits |
| --- | --- | --- |
| Classic Red, same five-nail hand, 20 steps | 365.375 s wall; 322.810 s model generation | About 88% in reported model generation; one preserved reference. |
| Same hand/style, 12 steps | 264.062 s wall; 226.060 s generation | One run, same original crop/compositor path. |
| Same hand/style, selected 8 steps | 221.000 s wall; 185.100 s generation | About 39.5% faster than the old 20-step reference; no outside-mask changes on this hand. Broad style/pose equivalence is not proven. |
| Representative Hair Consultation, 2026-09-30 | 68 / 64 / 65 s per look | Bob → Bun → Crew Cut, including TRAIN-001/TRAIN-002 switching. |
| Representative Makeup Consultation, 2026-09-30 | 66 / 66 / 70 s per look | Three different approved presets. |
| Representative Nails Consultation, 2026-09-30 | 234 / 12 / 204 s per look | Red model → French renderer → Black model; both model outputs edited five nails. |

Sources: [latency comparison](../experiments/nails-latency-comparison-20260928.md), [numeric review](../experiments/nails-latency-live-review-20260928.json), [representative Consultation](../experiments/CONSULTATION-02-live-gate.md), [Gate 2 review](../experiments/unified-kaggle-gate2-review.json).

**Already implemented:** hosted `scripts/render_kaggle_bootstrap.py` explicitly sets `NAILS_INFERENCE_STEPS=8`. The general backend default is still 20 for compatibility. Do not propose 20→8 as a new optimization or silently reduce Hair/Makeup's 20-step setting. The currently running private notebook's effective step metadata and present latency remain **Needs verification**; no GPU requests or account inspection were performed here.

### Where to investigate next

The original runtime calls supply a prompt string every time. The exact pinned Diffusers commit `c943837899b16cbae2f619b8dd4f7bb6f07dd81a` supports `prompt_embeds` and `negative_prompt_embeds`; its `encode_prompt` invokes the text encoder when no embedding is supplied. With guidance 4 on this non-distilled Base, both positive and empty negative prompts are encoded. Repeated fixed-prompt encoding across nail crops is therefore real repeated work; **its time share and achievable speedup are not yet measured**. [Pinned pipeline source](https://github.com/huggingface/diffusers/blob/c943837899b16cbae2f619b8dd4f7bb6f07dd81a/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py).

First candidate after measurement: reuse bounded **public style prompt** encodings, including the negative prompt, with keys/invalidation covering model/adapter/prompt hash, precision and encoder options. Never cache portraits, crop latents or cross-client results. Keep all existing prompts, random generators, image/crop dimensions, inference steps, masks, LoRA checks and worker ownership. Handle CPU offload hooks and cache RAM explicitly. This is a proposed experiment, not guaranteed equivalence or speed gain.

Second candidate only if phase timings justify it: reuse the existing isolated CPU segmentation runtime/model across requests rather than loading it in each invocation, with bounded lifecycle/timeouts and unchanged prediction/refinement rules. Compare exact masks and final composites before adoption. Do not combine multiple changes in the first comparison.

No new hardware/provider, quantization, distilled model, lower resolution, lower steps, unreviewed batching, GPU concurrency or renderer substitution is proposed in this release. A polling/connection-pooling tweak alone is not an adequate explanation or fix for multi-minute inference.

## 2. Descriptions and actual pricing

The generator's public style response already includes `description`. Makeup and Nails have usable short descriptions; some expanded Hair descriptions simply repeat the style name. Studio selection cards show descriptions, but the common generated-result dialog does not display the full style description. Consultation shows a recommendation reason (why suggested), which is different from a stable style description.

The booking/service source is `beautycore/lib/services.ts`. Individual service items contain **name and price only**; group intros are not descriptions of individual AI looks. Appointments record the actual selected service and amount. The project has no separate authoritative style-price table.

| Actual catalog entry | Recorded catalog price | How to use it honestly |
| --- | --- | --- |
| Men's Cut | ₱180 | Conditional estimate for that chosen booking service, not a universal Crew Cut tariff. |
| Women's Cut & Blowdry | ₱350 | Keep the service label; do not choose it by inferring a person's gender from their photo. |
| Children's Cut (under 12) | ₱150 | Only when the client chooses the applicable service. |
| Blowdry & Style | ₱250 | Candidate styling service; exact AI-style mapping needs confirmation. |
| Updo / Special Occasion | ₱500 | Candidate for an updo; mapping is proposed, not already configured. |
| Bridal Hair | From ₱1,500 | Preserve the starting-from qualifier. |
| Classic Manicure / Gel Manicure | ₱180 / ₱350 | Offer named service options; a polish color does not establish whether the service is classic or gel. |
| Nail Art (per nail) | From ₱50 per nail | Do not present as a whole-hand total or invent an add-on count. Confirm whether/when it is additional. |
| Makeup Application | Price to be confirmed | Numeric Makeup pricing is missing. Do not use ₱0 or the old demo price. |
| Perm-style curls and other unmapped directions | No verified per-style offering/quote | Description can be shown; mapping/price is Needs confirmation rather than substituting an unrelated service. |

**Conflicting demo metadata:** `backend/app/consultation/metadata.py` hardcodes Hair ₱600, Makeup ₱500, Nails ₱350 and demo durations, all marked `demo_only`. The web Consultation and native `mobile/app/consultation.tsx` render them. They are not approved salon prices; replace their product-facing price display with catalog-grounded information, without silently breaking existing strict mobile/API contracts that require numeric demo fields.

**Missing mapping:** current saved-look catalog in `beautycore/lib/business/style-catalog.json` has only three default Hair styles. Hosted startup selects `style_registry_train002_smoke.json` with thirteen. The existing catalog checker compares only the default registry, so it misses that mismatch. Expanded styles can generate but are rejected by the current save validator. The new resolver/checker must cover both configured catalogs and approved public style metadata. Do not enable new model styles merely by adding display metadata.

### Proposed metadata design

- Define one server-owned look-information resolver using public style IDs/descriptions and **the existing service catalog** for prices. Do not ask Gemini to invent prices or add another generative call for descriptions.
- Fill inadequate Hair descriptions with short editorial wording reviewed as descriptive copy, not claims that the exact text was already in the source. Reuse existing Makeup/Nails descriptions. Keep reasoning separate from description.
- Represent estimate kinds explicitly: fixed service option, starting-from, per-nail and quote-required. Support multiple named service options until a client chooses one. Missing mappings show **Price to be confirmed** plus suitable booking choices, not a fabricated price/range.
- A conditional example after approval: **Crew Cut — a short, easy-to-maintain haircut. Estimated cost: ₱180 if booking Men's Cut; other selected services use their catalog price.** This is proposed display copy/mapping, not an already verified style-specific tariff.
- Show the same information in standalone results, Consultation result/selected summary, Saved Looks, look-aware booking, and client/stylist/admin requested-look details. Booking must continue deriving the actual amount server-side from the selected service; saved estimates are not charges or payment records.
- Add one nullable `look_details` JSONB snapshot to the existing `ai_generations` record, containing server-derived description, named estimate options/kinds, currency and catalog version/capture time. Extend the atomic save function/validator/store and immutable-content rule. Do not store a second image or create a new history/price table. Preserve backward-compatible save calls during a future rollout.
- Existing saved looks with no snapshot use a clearly labeled **current catalog estimate** fallback; do not fabricate the historical quote or overwrite a booked reference. Duplicate saves retain the original snapshot; the booking form can separately show today's selected service price.
- Future approved database work is tested on isolated fixtures and supplied as an additive migration file. **No live migration in this planning task or unapproved rollout.**
- Native currently displays descriptions on standalone results and numeric demo estimates in Consultation. Proposed client UI slice is web-first, matching the previous Save/Book release. Preserve mobile payload contracts; coordinate a follow-up native display update with the same authoritative metadata before describing costs as consistent across web/mobile. No new native account Save/Book feature is implied.

## 3. Market Trends removal dependency map

| File/module | Action proposed | Keep working |
| --- | --- | --- |
| `beautycore/app/admin/market-trends/page.tsx` | Remove the active page; old direct URL returns the normal 404. | Admin layout/auth remain. |
| `beautycore/components/AdminSidebar.tsx` | Remove only Market Trends link and its now-unused local icon import. | Other portal links and shared Sidebar stay. |
| `beautycore/README.md` | Remove Market Trends from active feature/route documentation. | Historical audit/evidence remains historical. |
| `/api/admin/stats` | Retain. The Trends page consumes it, but so do Admin Finance and Dashboard. | Completed-only finance totals, top services, inventory/account aggregates. |
| `/api/generations`, `ai_generations`, `analysis_result` | Retain history/data. Trends reads only the signed-in account's limited history; it is not a dedicated market-wide analytics service. | Legacy generation, saved looks, appointment references and original analysis records. |
| Shared UI/Card/animation/icon packages | Retain. | Used throughout the app; an icon called TrendingUp elsewhere is not the Market Trends feature. |
| `_legacy_src` archived sidebar/Security references | Not active Next.js routes; do not refactor archive as runtime work. | No unrelated archived-code edits/dependency removals. |

No dedicated Market Trends database table, model, job or external provider was found. Removal needs no destructive database change.

## 4. Concise implementation sequence after review

1. **Baseline first:** use existing request/correlation diagnostics and Nails phase metadata; add bounded phase timing where missing (Render bridge/facade/job detection, adapter switch, positive/negative text encoding, image encode, denoising, decode, CPU geometry). Keep image contents/secrets out of logs. Verify actual running configuration before timing. Distinguish cold startup, first request, warm model request, and time to first/all Consultation results.
2. **One measured optimization:** profile the largest avoidable stage, start with fixed-prompt encoding reuse if material, and compare it in an isolated candidate against unchanged generation. Consider persistent CPU segmentation only if the measured CPU phase warrants it. Do not promise a target speedup before evidence. Retain the working notebook/bundles and rollback route.
3. **Look information:** implement the server-owned resolver/catalog synchronization, conditional prices and missing-price handling; add optional immutable snapshots and integrate result/gallery/booking/staff components. Keep numeric demo fields backward-compatible until native consumers are updated; remove misleading demo prices from the new web display.
4. **Remove Trends:** remove its active page and navigation/documentation references, retaining shared APIs and history.
5. **Verify locally and report:** collect before/after timing and quality evidence; run relevant Python, AI bridge, save/booking/finance, UI and migration tests, typecheck and production build. Report which goals pass and any remaining Needs verification. **No Render deployment, production database migration, replacement of working Kaggle services or automatic publication.**

## 5. Acceptance evidence

| Area | Required check |
| --- | --- |
| Speed | Same approved photo/style/adapter/hash/seed/steps/resolution/hardware, warm-up, at least three matched timed runs for chosen benchmark cases. Interleave baseline/candidate where practical. Report median and range, no p95 claim from tiny samples. Startup is separate; include full browser-visible completion as well as subphases. |
| Quality | Establish baseline repeatability first; require exact output/mask equality for work-reuse changes where baseline is deterministic. Otherwise flag differences for visual review rather than inventing tolerance. Inspect identity/hair/makeup and nail finish; require unchanged outside-mask pixels and all expected nails. |
| Cross-feature | Hair TRAIN-001 and TRAIN-002, Makeup, Red/Black model Nails, all three renderer styles, Hair restoration, and three-look Consultation. Keep one-owner/busy/cancellation/no-automatic-retry semantics. |
| Estimates | Fixed/from/per-nail/unknown values match actual named catalog services. Missing Makeup and unmapped style prices remain unknown, not zero. Changing price in the browser cannot alter server-derived saved metadata or booking amounts. |
| Persistence | New description/estimate snapshot survives reload and booking, account separation and gallery removal; assigned stylist sees the same booked reference. Old rows/no-snapshot fallback and duplicate saving remain valid. Catalog price changes do not rewrite historical snapshots. |
| Removal | No active Market Trends link/page; direct route 404. Finance, Dashboard, history, saved looks and role navigation still function. |
| Compatibility | Existing asynchronous/synchronous clients and native strict contracts still work. Web/mobile cost consistency is not claimed until the native display is updated/tested. |
| Release boundary | Reviewable local implementation only. No Render deployment or live schema/config/notebook mutation. |

## 6. Approved local implementation outcome

The Supervisor approved development with “lets start” and confirmed a separate private Kaggle GPU session is available for the comparison. The historical inspection/proposal above is retained to explain the decisions.

- **DONE / locally VERIFIED:** shared short descriptions and actual named catalog estimates in generated web results, Consultation, gallery, booking and requested-look details. Conditional service options avoid gender inference and unsupported style-specific tariffs. Makeup and unmapped curl/wave services remain quote-required; per-nail/from qualifiers remain visible.
- **DONE / locally VERIFIED:** immutable server-derived `look_details` snapshot in existing generation records, backward-compatible old save function, current-estimate fallback for old rows and expanded thirteen-style Hair catalog validation. Migration `0004_look_details.sql` is supplied and tested on disposable PGlite only; it has not been applied live.
- **DONE / locally VERIFIED:** active Market Trends route/sidebar removed; shared stats/history APIs, Finance and Dashboard retained.
- **EXPERIMENTAL:** optional phase timing and bounded CPU prompt-encoding reuse, disabled by default. A new private notebook reproduces the reviewed model/runtime and runs baseline/candidate comparisons without a server, tunnel or website registration. Existing working demo files remain intact. The completed private GPU result has since been independently reviewed: three-pair median reductions12.86%Crew,14.05%Makeup,22.47%Red single crop, all eleven pairs byte/pixel identical. Cold-cache and full application limits remain; see the benchmark review.
- **NEEDS VERIFICATION:** full-hand geometry/renderer and browser-visible cross-feature rehearsal, client-device visual acceptance, actual Makeup/missing prices and special Nail Art rules. The supplied worker paired timings and exact image equality are now verified for their bounded cases. Native numeric demo fields remain unchanged for compatibility; cross-platform price consistency is not claimed.

See the [development guide](../guides/generation-improvements-local-review.md) and [verification record](../experiments/generation-improvements-development-20261018.json). No Render deployment, live migration, cloud configuration change or push is included in this implementation.

## 7. Completed GPU worker review

The Supervisor returned the completed private benchmark ZIP. CRC/exact inventory, reported input hashes against the immutable approved bundle, all22 PNG/RGB hashes, eleven exact before/after image pairs and recomputed summary statistics pass independent checks. The repeated-use speed candidate is suitable for the next isolated application rehearsal; it remains disabled in the working demo. First-use caching shows no consistent speed gain; Bun/Black have only one cold pair. Nails timing is a single crop, not a five-nail result. No deployment or current runtime flag change is authorized by receipt of this report. [Review](../experiments/generation-speed-benchmark-20261018-review.md).

## 8. Focused application rehearsal preparation

Supervisor “proceed” confirms preparing the next isolated rehearsal. A separate private generated notebook now covers actual CPU API/gateway, one full1600x1200 five-nail hand, all renderer branches, Hair and Nails three-look generation, Makeup and Hair adapter restoration. It uses the existing deterministic recommendation provider for reproducible recommendations; no Gemini/browser/Render acceptance is claimed. Thirty model calls produce20application results in two modes, with mask/pixel/ownership/busy/provenance checks and explicit progress. Full484-test regression and final8focused tests pass locally with synthetic vision/GPU. Real user-run full-hand comparison/results are still NEEDS VERIFICATION. Existing demo/runtime flags and live database unchanged; no deployment. [Operator guide](../guides/application-rehearsal-20261018.md), [preparation evidence](../experiments/application-rehearsal-preparation-20261018.json).
