# BeautyCore expanded styles: architecture and deployment plan

Date: 30 October 2026  
Design: **CONFIRMED for implementation by Supervisor's proceed instruction**  
Release implementation: **IN PROGRESS; French Bob and three Nail additions approved and packaged locally; live rehearsal pending**  
Evidence: **VERIFIED local implementation; French Bob and three Nail designs human-approved on reviewed examples; other candidates held/untested**  
Scope: **CONFIRMED** â€” target all proposed Hair, Makeup and Nails styles; test Makeup before rollout.

This document preserves the release design and records subsequent implementation checkpoints. The planning task itself made no serving or cloud changes. The latest checkpoints distinguish prepared local artifacts from live deployment.

## 1. Outcome and release boundary

Keep the existing Render application, Neon persistence and scheduled Kaggle AI runtime. Extend the current selection, consultation, generation, saving and booking flow. No new AI service, authentication system or inventory module is needed.

Before this release, application metadata contained **13 Hair + 10 Makeup + 5 Nails = 28 styles**. French Bob and three accepted Nail additions now bring local metadata to **32 styles**: **14 Hair, 10 Makeup and 8 Nails**. Cloud deployment remains unverified. Expansion targets **5 Hair + 3 Makeup + 5 Nails = 13 candidates**. The eventual target is **18 Hair + 13 Makeup + 10 Nails = 41 styles**, only if every candidate passes. Counts describe checked-in catalogs, not an independent live website probe.

Selecting all candidates establishes scope; it does not override failed tests. All candidates may exist as inactive configuration while only accepted, installed and compatible styles are offered.

Use two release lanes:

- **Hair/Nails:** release accepted additions without waiting for a Makeup correction.
- **Makeup:** correct the original white cast, validate existing presets and additions, then release accepted entries.

Do not publish a misleading style name merely to reach 41. Record the failed criterion and hold that candidate. Do not substitute another look silently.

## 2. Actual architecture and proposed additions

The verified deployment configuration is [render.yaml](../../render.yaml). The Node/Next.js application under beautycore/ runs on Render. The Python API and shared GPU worker run in Kaggle. The separate frontend/ directory is not the Render blueprint's selected root.

~~~mermaid
flowchart TD
    U["Client browser"] --> R["Render: BeautyCore Next.js"]
    R --> B["Authentication, same-origin API proxy, guest limits"]
    R --> D["Neon: saved looks and appointments"]
    B --> T["Authenticated temporary tunnel"]
    T --> K["Kaggle: FastAPI facade, consultation and job admission"]
    K --> C["Active styles: approved and installed capabilities"]
    K --> G["One shared FLUX foundation; serialized adapter switching"]
    G --> H["Hair: existing TRAIN-001 / TRAIN-002"]
    G --> M["Makeup: existing MAKEUP-001"]
    G --> N["Model Nails: existing NAILS-001"]
    K --> V["CPU: landmarks, segmentation and finish rendering"]
    V --> P["Nail refinement and original-image compositing"]
    N --> P
    H --> O["Result: style ID, image and truthful provenance"]
    M --> O
    P --> O
    O --> K
    K --> T
    T --> B
    B --> U
    R --> S["Save look: image, description and price snapshot"]
    S --> D
    D --> A["Booking, client dashboard and assigned stylist"]
    X["Versioned style release manifest"] -.-> R
    X -.-> C
    X -.-> G
    X -.-> V
    K -.-> L["Existing signed registration and heartbeat"]
    L -.-> R
~~~

Manifest-driven Render metadata, active catalogs and the three CPU Nail profiles are implemented locally. Additional GPU execution profiles remain proposed. The browser continues calling same-origin Render routes. It does not receive AI keys or call the GPU directly. Renderer-only Nails need no diffusion call; existing shared admission policy stays intact.

### Verified boundaries

| Area | Actual source | Release implication |
|---|---|---|
| Render | render.yaml | Keep Node service; Python/model dependencies stay in Kaggle. |
| Browser proxy | beautycore/lib/ai/adapter-core.ts, studio-api.ts, studio-consultation-api.ts | Preserve routes, signed consultation handles, errors and job/status flow. |
| Discovery | beautycore/lib/ai/runtime-registry.ts, runtime-store.ts; app/api/internal/ai-runtime/register/route.ts; scripts/render_kaggle_registration.py | Keep automatic registration; no routine tunnel URL editing. |
| Kaggle facade | backend/app/demo_server.py, demo_gateway.py, deployment.py, main.py | Preserve authentication, shared admission and protected readiness. |
| Shared GPU | scripts/unified_gate3_server.py, unified_gate2.py | Keep one foundation and serialized adapter ownership. |
| Hair | backend/app/registry.py, styles.py, both style_registry JSON files; scripts/kaggle_inference_server.py | Current checkpoint style ownership is strict; appending IDs alone can fail. |
| Makeup | backend/app/makeup_contract.py, makeup_styles.py, generation/remote_makeup.py; scripts/makeup_inference_server.py | Separate frozen ten-preset metadata from new execution profiles. |
| Nails | backend/app/nails/styles.py, contract.py, render.py, hybrid.py | Add explicit renderer support; preserve model styles and refinement. |
| Consultation | backend/app/consultation/catalog.py, metadata.py | Active IDs require tags and correct model/renderer classification. |
| Business metadata | beautycore/lib/business/style-catalog.json, look-information.ts; beautycore/lib/services.ts | Every exposed style needs matching metadata and actual service mappings. |
| Persistence | beautycore/lib/business/core.ts, store.ts | Saves require a known style; image and look-details snapshots already exist. |
| Optimization | scripts/package_optimized_render_kaggle.py, optimized_demo_overlay.py, inference_performance.py | Preserve Nails-only prompt caching and baseline Hair/Makeup behavior. |

## 3. Per-style readiness

These candidate IDs already exist in the experimental shortlist. Retain them as stable IDs if promoted; the internal exp_ prefix does not require an experimental public name. Do not rename existing IDs or reinterpret historical saved looks.

| Candidate ID | Public name | Verified evidence | Required before release |
|---|---|---|---|
| exp_butterfly_cut | Butterfly Cut | HAIR-EXP-002 long inputs still become short bobs. | Held; correct shape before any promotion. |
| exp_wolf_cut | Wolf Cut | HAIR-EXP-002 produces excessive stiff spikes and recoloring. | Held; no approved natural preview. |
| exp_korean_two_block | Korean Two-Block | HAIR-EXP-002 yields dense fringe without established short-side separation. | Held; reliable two-block geometry required. |
| exp_comma_hair | Korean Comma Hair | Detached loops reduced, but Curtain similarity/eye coverage remain. | Held; distinct natural fringe required. |
| exp_french_bob_wispy | Textured French Bob with Wispy Bangs | Supervisor approves actual curly interpretation; preview may change hair color. Exact TRAIN-001 profile integrated locally. | Matching Render/Kaggle live rehearsal and rollout. |
| exp_cloud_berry_lips | Cloud-Skin Makeup with Blurred Berry Lips | Runtime passed; user rejected whiteness/blending; lip fidelity unresolved. | Correct complexion without a mask and show actual blurred lip styling. |
| exp_manga_lash | Manga-Lash Makeup | Not tested. | Grouped lashes without eye reshaping or drawn-on artifacts. |
| exp_icy_silver | Icy Silver Eye Makeup | Runtime passed; restraint, complexion and fidelity unresolved. | Localized silver accents, preserved face and acceptable overall balance. |
| exp_raspberry_jelly | Raspberry Jelly | Four-hand technical tests and human appearance approval; integrated locally. | Matching Render/Kaggle rehearsal and rollout. |
| exp_pink_aura | Pink Aura Ombré | Four-hand technical evidence and Supervisor approval; integrated locally. | Matching Render/Kaggle rehearsal and rollout. |
| exp_negative_space_microdots | Negative-Space Micro-Dots | Same technical evidence and human approval; integrated locally. | Matching Render/Kaggle rehearsal and rollout. |
| exp_milky_pearl_chrome | Milky Pearl Chrome | Not implemented/tested as a supported finish. | One bounded finish prototype; require pearlescence beyond gloss. |
| exp_dark_red_velvet_cat_eye | Dark-Red Velvet Cat-Eye | Not implemented/tested as a supported finish. | One bounded finish prototype; require a distinct luminous band. |

Nails evidence covers 12 outputs: four reused hands times three designs. Zero outside-refined-mask changes is a preservation check, not proof of correct anatomy or appearance. Pearl Chrome and Cat-Eye are not promised as simple palette changes.

Sources: [release review](../experiments/style-release-validation-20261025-review.md), [initial pilot review](../experiments/style-expansion-pilot-20261025-review.md), [validation record](../experiments/style-release-validation-20261025.json), and artifacts/style-expansion-20261025/automatic-mask-validation-02/report.json.

## 4. One controlled release manifest for additions

**Implemented locally:** backend/app/style_release.json is the checked-in, versioned expansion release manifest. Do not add a database or remote configuration service. Keep experimental outputs separate.

Each candidate record identifies:

- Feature, stable ID, public name and description.
- Execution path: Hair prompt profile, Makeup profile, or Nails renderer.
- Existing adapter identity where applicable; renderer version otherwise.
- Exact server-owned prompt/settings profile or renderer version and its hash.
- Validated input constraints, such as visible hair sides.
- Existing service names; prices remain in the real service catalog.
- Review status, evidence path and explicit production enablement.
- Release ID and compatible baseline profile.

Review status and executable availability are separate. A test pass must never set appearance approval. Failed/pending candidates start disabled.

Derive or validate Python additions and Next business metadata from this manifest. Avoid independent handwritten approval lists. Existing baseline catalogs and frozen artifact metadata remain authoritative for historical styles.

**Availability rule:** a new style must be approved, installed in the facade, supported by its execution path, and recognized by Render's deployed release. GPU capability applies to model routes; renderer-only Nails use CPU capability.

Enforce availability before direct generation, when building recommendations, and again before starting a recommendation job. Stale selections get a controlled unavailable-style response. Never fall through to another style or accept browser-supplied prompts.

Retain accepted historical business metadata after disabling generation. Reading a stored image and booking from an authorized saved snapshot are separate from generating that style again.

## 5. Feature design

### Hair

Reuse the verified foundation and existing adapters. Choose TRAIN-001 or TRAIN-002 per style from actual evidence.

Separate original training-artifact validation from new inference-profile validation:

1. Verify original checkpoint bytes, original metadata and training-label ownership against the original contract.
2. Load only accepted additional server-owned prompts from a versioned execution profile.
3. Verify that profile against the release manifest and selected adapter hash.
4. Return profile identity without claiming the new style was a training label.

The exact-style equality guard in read_adapter_metadata must not be bypassed. Refactor its inputs deliberately: original metadata stays checked against the original registry; the additional execution allowlist gets its own strict verifier. Update facade, GPU resolver and response checks together.

No new training is assumed. If existing adapters cannot produce an acceptable distinct style, hold it. New training requires a separate decision.

### Nails

Move the three validated experimental algorithms into the production Nails module with explicit IDs and deterministic tests. Do not import experiment scripts into serving routes.

Retain normalization, hand localization, automatic segmentation, source-resolution refinement, inward compositing and source geometry. Extend RENDERER_STYLES intentionally. Keep Classic Red and Glossy Black on their model route; preserve all five existing designs.

Implement Pearl Chrome and Velvet Cat-Eye independently behind disabled entries. Check finish fidelity and boundaries before enablement. A still image approximates appearance; do not claim physical magnetic behavior or changing reflections.

### Makeup: original white-cast correction

Do not deploy rejected Stable-Makeup outputs, the source-rendered replacement, or the visibly masked tone correction. Do not describe those as the trained model.

Inspect the original deployed path against archived controls: uploaded/normalized source, raw PNG, actual adapter/profile settings, compositing and browser display. Distinguish model complexion changes from normalization, post-processing or display problems. Exact causal contribution remains **Needs verification**; previous failures do not establish a safe parameter-only fix.

Write one concrete correction hypothesis and its limits before implementing a bounded comparison. Preserve the original control, adapter, resolution, seed and steps unless the hypothesis explicitly requires a change; record deviations.

Use four available, appropriately permitted photos spanning the available complexion/lighting variation, starting with Natural and Red Lip controls. Reused subjects are development evidence, not population-wide validation. Reuse exact matching historical controls. Do not launch another broad strength sweep.

Reject visible masks, whitening, unnatural transitions, face/feature changes, or cosmetics too faint to show the requested style. Pixel/color statistics alone cannot approve appearance.

If a correction passes, evaluate all ten existing presets and three expansion styles on at least two suitable inputs each. Include the previously rejected Berry case. Guidance 2.5 was relatively preferred earlier but did not establish a white-cast fix.

An accepted change gets a new execution profile, checked at worker, facade and client boundaries. Preserve frozen MAKEUP-001 checkpoint/preset verification. Do not rewrite training metadata to imply a revised inference profile was used in training.

Time-box diagnosis and the first bounded review. If no correction survives, record the blocker and hold Makeup changes. Do not automatically restart replacement-model, external-data or training work.

## 6. Consultation, prices, saving and booking

Keep existing routes and response shapes. Add accepted tags to backend/app/consultation/metadata.py. Ensure active_catalog excludes pending or incompatible entries. Gemini recommends from the available catalog; it must not invent supported IDs.

Existing flow remains:

1. User selects a style or completes consultation.
2. Facade validates availability and starts the existing job.
3. Result returns selected ID, image and truthful execution provenance.
4. Next resolves description and existing service options.
5. Save stores image, ID, name and look-details snapshot.
6. Booking references the saved look and follows service/stylist rules.
7. Client and assigned stylist retrieve the same stored image and details.

Do not duplicate images just because a style is new. Preserve authorization and booking references. Do not recompute captured descriptions/prices on every read.

Actual existing services include Women's Cut & Blowdry PHP350, Men's Cut PHP180, Classic Manicure PHP180 and Gel Manicure PHP350. These are options, not guaranteed prices for each new style. Nail Art is **from PHP50 per nail**, not a full-service quote. Makeup Application remains **Price to be confirmed**. Salon capability, extra finish charges and final mapping need confirmation. Do not use the backend consultation's demo-only 600/500/350 figures as actual salon prices.

Reuse LookDetails version 1 where sufficient. AI execution provenance does not itself require a new business table.

**No database migration is expected** for catalog additions. The inspected beautycore/db/schema.ts stores style IDs as varchar(80), names as varchar(255), and look details as JSONB. Migration 0004 accepts LookDetails version 1, caps its JSON size and makes stored content immutable. The proposed IDs fit these fields. Verify the implementation against these constraints; the live database migration state was not queried. No seed replacement or live-data rewrite is planned.

## 7. Matching deployment artifacts

Create a versioned CPU archive, GPU archive and client notebook from one source revision and accepted release manifest. Proposed names:

- beautycore-styles-cpu-<release>.bin
- beautycore-styles-gpu-<release>.bin
- notebooks/render_kaggle_expanded_styles_demo.ipynb

These are planned deliverables, not existing files. Preserve original archives/notebooks and the working optimized starter.

Build from an explicit, reviewable source snapshot and file allowlist. The current workspace contains substantial uncommitted experiments; do not stage the whole tree or include every experimental script in release archives. Include only required runtime sources/assets, accepted profiles and license records; exclude credentials, client photos, diagnostic outputs and unrelated changes.

Use additive packagers; old packagers contain historical names and must not overwrite old releases. Include exact inventories, per-file SHA256 hashes, archive hashes and matching release references. Check original model assets separately from new execution profiles.

The new notebook packages the final optimized worker directly. Do not layer an old optimized server file over a newer release. Preserve Nails-only prompt caching, invalidation and existing Nails inference settings. Keep AI_PROMPT_CACHE=1 and AI_PROMPT_CACHE_SCOPE=nails where already configured. Do not enable all-feature caching or reduce Hair/Makeup steps.

Startup verifies archive pair, environment, models, profiles, host RAM, CPU vision and one GPU foundation. Refuse duplicates, mismatched pairs, modified files and replacing a running service. Preserve isolated environments, MPLBACKEND=Agg and corrected pip bootstrap.

### Capability checks and dynamic registration

Current protected readiness checks feature-level readiness, one foundation and Nails settings; it does not prove every style works.

Add bounded protected readiness fields for release ID, catalog/profile digest and supported IDs grouped by path. Read actual loaded registries/renderers; do not echo a manifest without checking implementation. Cross-check facade/worker capabilities. Stay within the current 8192-byte verifier limit.

Update Render's verifyFacade to accept known compatible baseline or expanded releases, rejecting unknown/mismatched profiles. Missing expansion fields mean baseline support only.

Keep beautycore-runtime-v1 and its exact signed message fields unchanged. Put release information in protected readiness, not new unsigned browser input or a lease schema change. Preserve 60-second heartbeat, 180-second lease, replay checks and active-session refusal.

### Configuration

Keep existing settings; no routine Render changes are intended.

| Location | Existing settings | Treatment |
|---|---|---|
| Render | AI_BACKEND_MODE=kaggle; AI_ENDPOINT_MODE=registered | Keep automatic endpoint discovery. |
| Render | AI_BACKEND_API_KEY | Must match Kaggle; never expose to browser/packages. |
| Render | DATABASE_URL, SESSION_SECRET, AI_CONSULTATION_HANDLE_SECRET | Retain existing secrets. |
| Render | Guest-trial and saved-look settings | Retain current protections and allowances. |
| Kaggle Secrets | AI_BACKEND_API_KEY, AI_REMOTE_API_KEY, GEMINI_API_KEY | Enable in the new notebook; never print values. |
| Notebook | BeautyCore public website root | Keep the actual root for registration. |
| Bootstrap | Loopback URLs and execution settings | Generate from verified package; no client editing. |

No paid provider or new GPU service is proposed. Scheduled Kaggle sessions can still stop or lose their temporary tunnel; this is not 24/7 hosting.

## 8. Work sequence and completion gates

| Phase | Work | Exit criterion |
|---|---|---|
| 0. Baseline | Record revision, notebook/archive/model hashes, profiles, environment and representative outputs. | Reproducible rollback inventory and catalog parity. |
| 1. Shared contract | Manifest validation, catalog generation/checks and loaded capability reporting. | Pending IDs cannot generate or enter recommendations; old IDs work. |
| 2. Nails | Integrate three tested designs; prototype two new finishes separately. | Enabled designs pass appearance/mask review and real upload routes. |
| 3. Hair | Appropriate-input comparisons; accepted prompt profiles and ownership checks. | Enabled styles are distinct, plausible and correctly routed. |
| 4. Makeup | Original-path diagnosis, bounded correction, then full preset/expansion review if passed. | Human acceptance and regressions, or explicit hold. |
| 5. Business flow | Accepted metadata/tags/service mappings and save/book/dashboard checks. | Looks remain accessible after restart and disabling generation. |
| 6. Packages | Matching archives/notebook, inventories and fresh extraction tests. | No wrong pair, stale embedded code or false provenance. |
| 7. Rehearsal | Separate Kaggle session without overwriting an active registration. | Actual outputs, timings, switching and application flow pass. |
| 8. Rollout | Compatible Render first, matching Kaggle during a demo gap. | Accepted release registered and website checklist completed. |

Feature phases 2â€“4 share phase 1 but can ship independently. Makeup completion is not required for a Hair/Nails partial release. A single all-style release requires every candidate to pass; no completion date is justified by current evidence.

## 9. Verification

Extend existing tests; do not weaken provenance assertions:

- Exact catalog IDs, names, descriptions, tags and service mappings; no duplicate or pending public entries.
- Wrong-feature, unsupported and stale recommendation IDs rejected before job admission.
- Frozen Hair checkpoint ownership plus separately verified additional execution profiles.
- Makeup wrong hash/profile/settings and arbitrary-prompt rejection.
- New renderer Nails make no GPU calls; original model routes remain.
- Source geometry, refinement, outside-mask preservation, determinism and segmentation failure.
- Shared admission, cancellation, status polling, adapter restoration and no automatic generation retries.
- Compatible baseline/new registration; reject mismatched capabilities without changing lease/replay behavior.
- Save manual/consultation results; preserve snapshots and role-based image access.
- Stop Kaggle/disable style without losing saved images or existing bookings.
- Registered users and one-image guests retain existing limits.
- Tampered archives, duplicate inputs, mismatched pairs and stale notebook source fail early.

Existing implementation-check commands:

~~~text
Repository root:
python scripts/check_saved_look_catalog.py

backend/:
python -m pytest tests -q

beautycore/:
npm ci --include=dev
npm run typecheck
npm run build
npm run test:business
npm run test:guest-trial
node --experimental-test-module-mocks --import tsx --test tests/ai-runtime-registry.test.ts
~~~

Use the Python environment containing the appropriate installed dependencies. These are planned checks, not results from this planning task. The package currently defines npm run lint as next lint; verify a supported lint command before calling it a successful check.

### Appearance, performance and website checks

Retain each input, nearest baseline, candidate output, profile hashes, timings and verdict. Use suitable inputs and at least two examples per new Hair/Makeup style. Reuse the four-hand evidence for the three tested Nails and add production-route upload checks. Record human approval per style.

Run old Hair, new Hair, accepted Makeup, model Nails, renderer Nails, then old Hair again. Verify restoration and one foundation load. If Makeup changes are held, use unchanged baseline Makeup for compatibility only and record its limitation.

Measure cold setup, warm inference, adapter switching, segmentation/rendering, total job time and memory separately. Use baseline controls on the same session/hardware. More catalog entries do not imply faster generation. Standalone replacement-model timing is not a deployment benchmark.

The existing Render proxy has a 90-second upstream timeout. Verify actual job submission/polling; do not add long synchronous generation requests, raise timeouts blindly or automatically replay accepted work.

For each enabled feature, test selection/generation, description/estimate, saving, reloading, booking with an eligible stylist, client view, assigned-stylist view and existing completion/review rules. Include guest limit, busy response, stopped-Kaggle state and recovery. Unperformed checks stay marked as unperformed.

## 10. Rollout and rollback

1. Finish accepted subset, checks, package hashes and review evidence.
2. Deploy backward-compatible Render code recognizing baseline and expanded releases and accepted new metadata. Old Kaggle remains usable; new styles wait for matching capabilities.
3. Rehearse the new Kaggle package without registering over another active session.
4. Choose a demo gap. Finish existing jobs and save required outputs; end old session cleanly.
5. Start the new pinned client notebook. Attach exactly one matching archive of each type, enable Secrets, select reviewed GPU/environment and Internet, and run cells once in order.
6. Wait for readiness and automatic registration. A prior active lease can refuse takeover; let its 180-second lease expire after heartbeat stops. Do not force the database record.
7. Verify actual website styles, execution paths, consultation, saved looks and booking. Connected status alone is not acceptance.
8. Hand over the tested notebook version, exact inputs, enabled-style list, startup/restart checklist, known limits and fallback version.

A controlled AI interruption is expected during switching. No zero-downtime claim is made. The client device needs a browser; their Kaggle account still needs suitable GPU access, inputs and enabled Secrets.

If runtime fails, stop it, preserve logs/results, wait for lease expiry where necessary and start the preserved working notebook. Keep compatible Render bridge code: it should accept baseline capability while retaining metadata for new saved looks.

If application rollback is necessary, use a version proven to read new snapshots/bookings. Test before release; do not blindly roll back to code that cannot recognize new saved IDs. Never delete saved images or appointments to roll back generation.

## 11. Deliverables and unresolved items

Implementation deliverables:

- Versioned manifest covering all 13 targets and their dispositions.
- Accepted production catalogs, execution profiles/routes and regression tests.
- Separate Makeup correction evidence and accepted/held verdict.
- Matching CPU/GPU archives, notebook and generated SHA256 inventory.
- Website rehearsal and rollback verification records.
- Short client guide requiring no routine Render URL editing.

Unresolved: remaining candidates' appearance acceptance, untested Hair/finish capability, successful Makeup correction, salon capability and extra charges. Appearance approval is recorded for the three reviewed Nail designs only. Current provider quotas and live runtime health were not independently verified here.

No replacement model, paid API, training run, database migration or wider architecture redesign is adopted by this plan.

## 12. Planning verification receipt

Source inspection verified catalog counts, strict model ownership, active consultation filtering, snapshot persistence, registration, shared GPU boundaries and the optimized starter mechanism.

The model-free command **python scripts/check_saved_look_catalog.py passed**: current business metadata matches both Hair registries, Makeup and Nails.

No model load, image generation, GPU call, production query, build, deployment or end-to-end test ran during planning. Proposed release behavior still requires implementation and validation.

Historical reference: [integration map](../experiments/style-release-integration-map-20261025.md). Later Makeup rejection overrides earlier optimistic promotion recommendations.


## Implementation checkpoint — 30 October 2026

The release manifest, strict profile/capability verification, Render compatibility and three gated Nails renderer integrations are implemented and tested locally. All additions remain disabled pending Supervisor review. Full execution-profile support for new Hair/Makeup, remaining finishes, new Kaggle packages and rollout remain incomplete. [Milestone evidence](../experiments/expanded-style-milestone1-20261030.md).


## Accepted Nails and release package checkpoint — 30 October 2026

The Supervisor approves the repaired gallery: "I approve the design it looks good." This accepts Raspberry Jelly, Pink Aura Ombré and Negative-Space Micro-Dots on the reviewed examples. Only those three manifest entries are accepted/enabled locally; the other ten candidates stay held or untested.

Generated business metadata includes the same descriptions and existing manicure/per-nail service options. New regression checks exercise each accepted style through saved-look admission, real disposable-database booking, persisted snapshots and private image access from client/assigned-stylist responses.

A separate immutable CPU archive and new optimized starter have been prepared. The original GPU archive, model sources/settings, original CPU input and both fallback notebooks remain unchanged. The new starter verifies the archive/member hashes, exact release pair and loaded facade release before registration. The existing Nails-only cache and signed registration protocol remain intact.

Matching Render publication/deployment and a fresh Kaggle/website rehearsal are still required. No source push, cloud deploy, new GPU run or database migration occurred in this preparation. [Operator guide](../guides/expanded-nails-release-20261030.md), [approval](../experiments/expanded-nails-approval-20261030.json), [package inventory](../experiments/expanded-nails-package-20261030.json).


## Hair validation preparation checkpoint — 30 October 2026

Supervisor requests proceeding to Hair. HAIR-EXP-002 prepares21fixedcalls: five candidates on two suitable historical sources each, ten nearest-baseline controls and one exact adapter-restoration repeat. Butterfly/French Bob use TRAIN-001; Wolf/Two-Block/Comma use TRAIN-002 as test choices. Keep original checkpoint/training-label guards and existing quality settings. Comma has one geometry-focused prompt correction; no strength/adapter sweep or new training.

A separate private notebook, original GPU input only, is prepared with original environment/model checks, partial evidence ZIP and self-contained review images. Twelve new and23related checks pass locally; actual GPU outputs/appearance remain unverified. All Hair entries stay held/untested and disabled. Accepted Nail manifest/package metadata and application code remain unchanged. Per-style visual acceptance still precedes production execution-profile support and matching release packages. [Guide](../guides/hair-expansion-validation.md), [evidence](../experiments/hair-expansion-preparation-20261030.md).


## Hair result review checkpoint — 31 October 2026

HAIR-EXP-002 completes21calls with exact sources/settings/runtime/adapter-state and restoration checks. All five comparison sheets were reviewed. Butterfly fails long-layer shape; Wolf is excessively spiky; Two-Block lacks established lower-side separation and covers eyes; Comma reduces detached loops but remains too close to Curtain with eye coverage. French Bob is the closest candidate, with a curly interpretation and source-color changes requiring client/stylist review and explicit limits. No new Hair appearance is accepted or enabled.

The original five-candidate readiness table is historical; this returned batch supplies current first-test evidence for Wolf/French Bob and additional failed/qualified evidence for the other three. Preserve current tested profiles in the experiment record rather than adding unsupported IDs to the trained model registry. No production implementation or new sweep is authorized by a returned ZIP. The approved immutable Nail release remains unchanged. [Detailed review](../experiments/hair-expansion-results-20261031-review.md).


## Approved French Bob integration checkpoint — 31 October 2026

Supervisor says "i APPROVE IT" after French Bob was singled out for review. Approval is recorded for that candidate and its actual curly/color-changing preview. The other four Hair additions stay held.

New hair_profile.json and hair_profiles.py define the exact reviewed prompt/settings, original TRAIN-001 checkpoint ownership and an additional inference-profile contract without adding historical training labels. Public remote Hair discovery/generation and consultation use the approved profile. Worker-side hair_release_worker.py extends only a fresh, verified release workspace; original worker source, training registries and original generation methods stay preserved. New output provenance states trained_style:false for this inference addition.

Both protected worker reports must advertise the matching release, model styles and profile hashes. The facade rejects missing/old/mismatched worker evidence or incorrect result provenance. Render recognizes the exact new release plus the preserved Nail-only release, keeping truthful fallback catalogs and saved metadata.

The separately named combined CPU input and starter include French Bob, the three approved Nails and the existing Nails-only optimization. Original GPU/checkpoints/registries/old CPU inputs/notebooks are preserved. Saving, real catalog-priced booking and private client/assigned-stylist preview are covered by tests. No database migration, GitHub publication, Render deployment or new GPU run is performed by this local preparation. Live GPU/browser rehearsal remains mandatory. [Run guide](../guides/hair-nails-release-20261031.md).


## Broad approval and Makeup completion checkpoint — 31 October 2026

Supervisor explicitly approves all expanded Hair and Nail designs, overriding the earlier French-only interpretation and Codex appearance holds for other reviewed Hair looks. All five Hair outputs are accepted as shown; known shape/recoloring limits remain factual and must be described truthfully. All five Nail designs are approved scope, while Pearl Chrome/Cat-Eye still lack implemented/tested renderers. Remaining approved Hair routes and unimplemented finishes require a new version and technical integration; do not alter the immutable French+Nails package or bypass original checkpoint/profile guards.

Attention moves to Makeup. Existing saved outputs now have a verified64imagegallery; whitecast remains unresolved. MAKEUP-EXP-002 prepares only the missing Manga Lash test: one exact Soft Glam control and two Manga images, retaining six already verified Soft/Berry/Icy outputs. No extra setting sweep, replacement method, training or whitening-fix claim. Eleven local checks pass; actual GPU result and Makeup selection remain pending. [Approval](../experiments/all-hair-nails-approval-20261031.json), [guide](../guides/makeup-expansion-completion.md).


## Makeup completion result checkpoint — 31 October 2026

MAKEUP-EXP-002 completed one exact Soft Glam control and two Manga Lash outputs; six Soft/Berry/Icy reference outputs remain unchanged. All three expanded Makeup candidates now have two reused-source development outputs. Technical integrity and pinned runtime checks pass, but this is not acceptance or a complexion correction. Both Manga outputs still lighten/smooth the source face and alter facial details. New Makeup remains pending client review; Codex recommends holding public release against the original white-cast requirement.

No serving settings/catalogs or sealed release packages changed. Experimental guidance2.5 does not replace the existing4.0contract. All-five Hair approval and all-five Nail design scope remain authoritative; remaining routes/finishes need their separate technical integration. [Result evidence](../experiments/makeup-expansion-results-20261031-review.md).


## Five-Hair/three-Nails publication checkpoint — 31 October 2026

User explicitly chooses integrating all five approved haircuts before deploying with the three tested Nail designs. Release styles-20261031-02 now implements all five exact reviewed profiles, correct TRAIN-001/TRAIN-002 routing, strict result provenance and truthful baseline-only fallback catalogs. Existing model registries/checkpoints and Makeup settings remain unchanged. Public descriptions disclose reviewed Hair limitations. Real save/book/private client/assigned-stylist tests cover all eight additions.

A separately named CPU input and new three-cell optimized starter preserve previous immutable packages and authenticated automatic endpoint registration. Current Render source recognizes current and preserved exact releases. Source published at63fc851 on codex/render-kaggle-demo; operator must deploy matching Render commit before starting the new Kaggle notebook. Local checks pass after correcting one historical test's obsolete assumption that approved styles remain absent. No new live GPU generation, website rehearsal, secrets or database migration claimed. Full cloud release acceptance is pending those operator/live checks. [Guide](../guides/all-hair-nails-release-20261031.md).


## Separate Makeup correction checkpoint — 1 November 2026

The original skin-tone blending requirement is active again. A separate offline source-referenced color-field prototype now has ten saved-result comparisons, including four at the deployed model setting. It reduces visible pale cast while retaining cosmetics, but possible warmth/edge shifts and the model's texture/geometry changes remain. Appearance is pending human review; no existing/new Makeup style, serving contract or dependency was changed. Hair/Nail release63fc851 and its packages remain unchanged. Do not promote this prototype or infer expansion readiness from its23technicalchecks. [Evidence](../experiments/makeup-complexion-20261101.md).


## Source-fidelity refinement checkpoint — 1 November 2026

Supervisor acknowledges improved complexion color but requires the same natural original photo with minimum retouching. A separate original-canvas subtle-color pilot now preserves original facial detail, luma and protected regions rather than retaining a regenerated face. Two examples/18checks and full-size toggles are available for review. No universal appearance approval, full Makeup style support or production replacement is inferred. Keep the existing Hair/Nail release and raw Makeup service unchanged while this source-fidelity requirement is evaluated. [Evidence](../experiments/makeup-source-faithful-20261101.md).

## Makeup preservation correction — 1 November 2026

**CONFIRMED requirement; IN PROGRESS fix; production integration NOT STARTED.** Natural complexion correction must preserve selected makeup and original person together. User explicitly rejects source-only subtle retouch for removing makeup; prior source-subtlety interpretation does not supersede makeup visibility. User requests all three offered references (Natural, Cloud/Berry and Classic Red Lip).

Offline cosmetic-layer v3 completes six cases with exact source-protection/reproduction checks but fails appearance: colored cheek patches, pasted transitions and incomplete eyes. No promotion, new generation or live changes. Next gate is reliable cosmetic separation, not further strength/guidance sweeps. Existing Hair/Nail rollout remains independent. [Evidence](../experiments/makeup-selected-cosmetics-20261101.md).

## Targeted Makeup repair checkpoint, 1 November 2026

**DONE offline repair/verification; full cosmetic fidelity IN PROGRESS; integration NOT STARTED.** User authorized planning and proceeding. MAKEUP-SEPARATION-001 v2.1 fixes reproduced highlight/ratio confusion, mask transitions and five-pixel Lab-round-trip no-op error. Six native comparisons,19focusedchecks/sixreproductions and48imageembeddedgalleryQA pass technically. Appearance remains experimental: selected lash density/shape, brow fill and blush intensity differ. No accepted universal or all-style fix. Production parsing/landmark assets, broader input/style checks and Kaggle cost validation remain required. No serving/Git/DB/cloud changes; Hair/Nail release remains separate. [Evidence](../experiments/makeup-separation-20261101.md).

## Visible selected Makeup checkpoint, 1 November 2026

**DONE local refinement and verification; appearance EXPERIMENTAL; production integration NOT STARTED.** User requests stronger recognizable selected makeup after rejecting prior visibility. MAKEUP-REFERENCE-001 v4.1 produces six comparisons with stronger selected color and actual lash detail while protecting original photo regions and leaving prior lipstick RGB unchanged.34checks/sixlatestreproductions/54embeddedgalleryQA pass technically. Perceived color on darker source, lash/brow fidelity and overall naturalness need human review. No new inference/model/dependency/DB/Git/cloud change. Runtime assets, fresh inputs/styles and Kaggle memory/total latency remain release gates. [Evidence](../experiments/makeup-reference-visibility-20261101.md).


## Makeup realism gate, 2 November 2026

Current reference transfer is **REJECTED**, not ready for integration. The original photo must remain the canvas, with unchanged source eyebrows and feature geometry. Six case audit finds pasted lipstick/cheek treatment and uncertain lip boundaries. Generated style guides are not separate cosmetic layers or reference ground truth. Next gate is source lip boundary and pigment isolation, not another global intensity or full face regeneration. Hair/Nail release remains independent and unchanged. [Evidence and bounded plan](../experiments/makeup-realism-audit-20261102.md).


## Source surface implementation checkpoint, 2 November 2026

**DONE bounded lip component, IN PROGRESS full Makeup, integration NOT STARTED.** New original canvas lip correction and reproducible evaluator have51passingchecks (17new). All six combined eye/cheek probes fail appearance and are preserved as rejected evidence. Lip only is not the finished requested look or a production replacement. Existing Hair/Nail release and current Makeup service unchanged. PROPOSED next direction is artist/salon approved explicit cosmetic layers fitted to source features, with actual full look validation before integration. [Evidence](../experiments/makeup-source-surface-20261102.md).


## Preferred lip component retained, 3 November 2026

**DONE review / no rendering change justified / full Makeup IN PROGRESS / integration NOT STARTED.** User confirms the lip only result as the improved direction. Six source comparisons and 17 focused checks support retaining that exact version. Edge and shade limits remain; no full Makeup or deployment approval is inferred. No working system code or model changed. [Review](../experiments/makeup-retained-review-20261103.md).
