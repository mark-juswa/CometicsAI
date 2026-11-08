# Decision history

2026-11-08, PROPOSED: validate a separate RTX A6000 candidate using the existing Runpod architecture after repeated 3090 allocation failures and user reported A6000 availability signals. Local image preparation is complete; this does not approve paid deployment, new output quality or website cutover. Preserve original 3090 and Kaggle paths. [Candidate](../docs/experiments/runpod-a6000-candidate-20261108.md).

2026-10-09, CONFIRMED: Supervisor selects Render + Kaggle for the scheduled capstone demo after hosting research, accepts the necessary changes, and confirms `mark-juswa/CometicsAI` as the deployment repository. Render hosts full BeautyCore with existing Neon; a new private Kaggle notebook hosts the CPU API/Nails tools plus the unchanged verified GPU bundle. Add explicit remote authentication/ownership and background generation with status/result reads; retain the local default and old notebooks/bundles as rollback. No paid upgrade, database migration, model/adapter change, silent retry/failover, or 24/7 uptime claim. Real cloud/resource/mobile gates remain open. [Contract](../docs/specs/0008-render-kaggle-demo.md).

2026-10-03, CONFIRMED: Supervisor requests a mobile-only Consultation UI refinement based on the finished BeautyCore web Consultation screenshots, prioritizing fewer visible controls and a lighter flow. Service presents service choice and Continue; Direction handles photo and one open description, with structured preferences optional; Your Looks focuses one of the three existing backend recommendations at a time. Existing authenticated Consultation lifecycle, AI behavior, web UX and generation contracts remain authoritative. This explicitly supersedes the MOBILE-02A Consultation placement of photo selection in Service and default visible preference controls; it is not a new Consultation architecture. Supervisor performs phone taps manually. [Evidence](../docs/experiments/mobile-consultation-ux.md).

2026-10-03, CONFIRMED: Supervisor explicitly authorizes MOBILE-02C real mobile Consultation, preserving Service → Direction → Your Looks and reusing existing BeautyCore Client identity/Origin, signed user bound handles, private FastAPI Consultation, text only Gemini, backend recommendation validation, existing generation dispatcher and unified Kaggle worker. Exactly three backend validated recommendations, one representative recommended Hair generation displayed on Android, Select and Custom handoff close this gate. Standalone Android Makeup visual acceptance and standalone Android Nails live generation acceptance are explicitly deferred and do not block MOBILE-02C. No redesign, parallel Consultation system, booking/payment, provider/model changes, automatic GPU retry or additional feature work. Manual phone actions only; previous remote phone restriction persists. [Integration](../docs/guides/mobile-02c-integration.md), [evidence](../docs/experiments/mobile-02c.md).

2026-10-03, CONFIRMED: Supervisor authorizes MOBILE-02B authenticated real Hair/Makeup/Nails generation through existing BeautyCore → private FastAPI → existing Kaggle, preserving browser auth/roles/Origin, all AI settings and MOBILE-02A UI. Reuse existing native cookie behavior after live testing, with only client NextURL Origin normalization and SDK File upload compatibility corrections. A minimal mobile launcher application-boundary mode is allowed; existing root launchers remain unchanged. Supervisor later defers Makeup/Nails evaluation and selects “Core reliability and finish current checks”; complete real Android Nails, Makeup visual acceptance and explicit native logout confirmation remain pending. Do not count server 200 or fixture results as full phone acceptance. No automatic MOBILE-02C or further GPU testing after this deferral. Remote phone restriction persists. [Integration record](../docs/guides/mobile-02b-integration.md), [evidence](../docs/experiments/mobile-02b.md).


2026-10-03, CONFIRMED: Supervisor requests MOBILE-02A product UX/UI before real generation: dominant Home AI Beauty Consultation, secondary Custom Hair/Makeup/Nails, header Settings with relocated diagnostics, shared Photo → Style → Review, dedicated mock comparison retaining photo for Try Another and clearing only that studio for Start Over, and mobile-native local Service → Direction → Your Looks using actual BeautyCore design/preferences. Preserve all backend/web/AI/launcher behavior; no fake AI or real generation. Supervisor selected Skip for optional independent spec review and deferred the new manual phone acceptance (“ill do this later”). Remote phone restriction remains active. [Spec](../docs/specs/0007-mobile-product-ux.md), [evidence](../docs/experiments/mobile-02a.md).

2026-10-03, CONFIRMED: Supervisor will perform physical Android acceptance actions manually and explicitly prohibits remote taps because of security concerns. Stop remote phone input/navigation and further phone screenshots. Do not enable or bypass Xiaomi's separate security debugging permission. Keep PC launcher/API assistance and ordinary USB reverse connectivity available; record manual results separately from previously observed native loading/health/catalog evidence. [Native evidence](../docs/experiments/mobile-native-android.md).

2026-10-03, CONFIRMED: Supervisor requests an additive Windows mobile development launcher before MOBILE-02, preferring authorized ADB reverse with a fixed loopback origin, then default-route LAN discovery. Resolve addresses automatically, pass the API origin only to Expo, start a separate FastAPI instance on 8001, fail clearly without restart loops or unrelated process kills, and provide safe owned Stop when practical. Do not rewrite env files or change working root launcher, backend configuration, BeautyCore, Gemini, models, Kaggle, generation contracts or MOBILE-01 feature scope. Native Android acceptance remains required; no available phone means MOBILE_01_BLOCKED. Implementation requires trusted Private/domain LAN and makes no firewall/profile/tunnel change. [Spec addendum](../docs/specs/0006-mobile-foundation.md), [evidence](../docs/experiments/mobile-launcher.md).

2026-10-02, CONFIRMED: MOBILE-00/MOBILE-01 is an additive Expo, React Native, TypeScript and Expo Router application under `mobile/`, translated from the existing web studio design. Supervisor explicitly selected existing FastAPI directly for development-only health/catalog integration; BeautyCore native authentication is deferred to MOBILE-02. Mobile never calls Kaggle or contains worker/server credentials. MOBILE-01 has local gallery drafts and unchanged mock results, no real generation, complete Consultation, camera, model conversion/retraining/quantization or inference change. Supervisor chose to leave Android device acceptance pending when no AVD or device was available. The existing authenticated web adapter/private FastAPI architecture is preserved; this is a bounded development exception, not production exposure approval. [Spec](../docs/specs/0006-mobile-foundation.md), [evidence](../docs/experiments/MOBILE-01.md).

2026-10-02, CONFIRMED: The unified BeautyCore Client must use the tested HAIR Consultation, Hairstyle, Makeup and Nails frontend experience. The old BeautyCore Advisor and preset builders are superseded as Client entry points; the old Advisor URL redirects to Consultation. Keep BeautyCore's authenticated `/api/ai/*` adapter, roles and business workflows; do not expose FastAPI directly to the browser. Admin historical generation reporting remains intact. This subsequent Supervisor instruction supersedes the earlier source import's temporary protection of the old Advisor UI. [Local evidence](../docs/experiments/beautycore-original-ai-ui-local.md).

2026-10-02, CONFIRMED: The client handoff target is one local BeautyCore project folder and one user facing BeautyCore application, preserving the existing FastAPI AI backend as a private local process in that folder. The Supervisor chose to retain the existing Kaggle notebook as the capstone's external GPU service. The approved direction is to import the actual BeautyCore source into the HAIR repository, not recreate the AI generators or migrate GPU providers. Live acceptance remains a separate gate. See [decision spec](../docs/specs/0005-unified-beautycore-folder.md).

2026-09-30, CONFIRMED: The Consultation page presents Service, Direction and Your Looks as successive client states on the existing route. Validated recommendations wait for an explicit visual-generation action; generation remains sequential through the existing API. Custom keeps the existing manual pages and photo handoff. This is presentation only; Gemini, backend validation, estimates and AI runtimes remain authoritative and unchanged. [Evidence](../docs/experiments/consultation-step-ux.md).

2026-09-30, CONFIRMED: CONSULTATION-03 selects `deterministic` or text-only `gemini` explicitly through backend configuration. Gemini's model/key remain server-side and its candidate input contains only text preferences/conversation plus active editorial style metadata, never the uploaded photo. Gemini proposals cannot bypass the existing three-style validator or set prices/durations; no silent fallback, provider/GPU generation retry or change to Hair/Makeup/Nails inference. The configurable default Gemini model is `gemini-3.5-flash-lite`; the earlier `gemini-3.8-flash` default is DEPRECATED after structured-output HTTP 503 evidence. Hair, Makeup and Nails live text-only conversations and local/mock implementation are VERIFIED; combined Gemini-to-GPU demo rehearsal remains NEEDS VERIFICATION. [Evidence](../docs/experiments/CONSULTATION-03.md).

2026-09-30, CONFIRMED: CONSULTATION-02 generates only the three primary recommendations, sequentially, via the existing central feature dispatcher after current-catalog revalidation. Generation statuses and one result per completed look remain in the bounded process-local consultation store; the general state response excludes image payloads. No automatic generation retry; a lost response is resolved with status reads and user-controlled retry is available only for recorded failures. Custom reuses the existing feature pages with one-navigation in-memory File transfer. Complements are displayed without image generation. No LLM, booking, GPU/runtime change or durable storage in this phase. [Architecture](../docs/specs/0004-consultation-generation-integration.md); [evidence](../docs/experiments/CONSULTATION-02-local.md).

2026-09-30, CONFIRMED: CONSULTATION-01 is an additive CPU-only orchestration foundation. Backend state and active feature catalogs are authoritative; a deterministic provider proposes styles, and strict backend validation resolves only enabled style IDs plus demo-only price/duration. No real LLM, GPU generation, booking availability, database migration, or Custom page rewrite in this phase. Process-local photo/state retention is explicitly limited to 10 consultations and one hour, so persistent deployment needs an authenticated retention design. [Architecture](../docs/specs/0003-consultation-foundation.md); [evidence](../docs/experiments/CONSULTATION-01-local.md).

2026-09-28, CONFIRMED: The three AI pages adopt the existing Andrea's clinic visual language from `F:\HAIR UI\beautycore`. Generation uses an honest indeterminate processing state and a two-column result dialog with download, close and regenerate. Keep feature controls and the central AI contract intact; this UI change does not alter inference or quality. The implementation is locally verified, while live model requests through the redesigned pages remain NEEDS VERIFICATION.

2026-09-28, CONFIRMED: Supervisor selected preparation of TRAIN-002 support after the Bun catalog mismatch. Add the existing verified artifact and approved optional registry to one separate private capstone candidate; preserve original package, worker/ownership and separate runtime fallback. Select local catalog from signed attached bundle identity, never route unsupported styles to TRAIN-001. Local preparation VERIFIED, unified GPU inference NEEDS VERIFICATION. [Evidence](../docs/experiments/capstone-train002.md).

2026-09-28 startup correction, CONFIRMED: wait for exact ready publication cache visibility before reporting CAPSTONE_AI_READY. Bounded metadata polling is permitted; generation retries remain zero. Never use an older ready endpoint. Same kernel entry refreshes startup support only and verifies/reuses the running worker. Evidence: [startup correction](../docs/experiments/capstone-startup.md).

Source for all entries: Supervisor's CODEX HANDOFF 001. Decision dates before this record: UNKNOWN. Recorded 2026-09-21.

| Decision | Status | Evidence | Rationale and authority |
| --- | --- | --- | --- |
| Compare Nails model generation at 12 and 8 steps, use 8 in the current local app after measured comparison | CONFIRMED | LIVE FIXED-CASE VERIFIED: 12/8 took 264.062/221.000 seconds versus saved 20 at 365.375; correct provenance and zero outside-mask changes, comparable gloss on the reported Classic Red hand | Supervisor authorizes optimizing the six-minute Nails generation. Current local configuration selects 8, about 39.5% faster in this observation; code default and original runtime remain 20 for reference/rollback. Models, prompts, seed, guidance, crop/mask processing and Hair/Makeup unchanged. Reduced-step Black/all-pose quality not claimed. [Experiment/evidence](../docs/experiments/nails-latency-comparison-20260928.md). |
| Project-trained conditional hairstyle Edit-LoRA on FLUX.2 Klein Base 4B directly generates the first demo result | CONFIRMED | EXP-001 mechanics VERIFIED; real model NOT STARTED | Supervisor's current critical-path direction requires one LoRA for three approved styles and direct pixel generation through the existing engine boundary. |
| Plain pretrained Klein refinement after custom generation | PROPOSED | NEEDS VERIFICATION | Earlier direction deferred beyond the first working demo by the Supervisor; it is not a DATA-001, TRAIN-001, or demo gate. |
| Free Kaggle GPU as training target | CONFIRMED | VERIFIED for EXP-001 smoke test | Supervisor's $0 constraint; one Kaggle T4 completed 20 finite-loss BF16 Edit-LoRA steps. Training-time risk remains. |
| Roughly six styles and 60 train plus 12 validation pairs | PROPOSED | NEEDS VERIFICATION | Preliminary dataset scale, not inspected data. |
| Synthetic source paired with real hairstyle target | PROPOSED | NEEDS VERIFICATION | Possible way to obtain paired edits under deadline. |
| Next.js/Vercel Hobby frontend and Gradio/Hugging Face Space with ZeroGPU if eligible | PROPOSED | NEEDS VERIFICATION | Free deployment direction; access and compatibility unproven. |
| Local System MVP using Next.js, TypeScript, Tailwind CSS, FastAPI, and a replaceable MockEngine | CONFIRMED | VERIFIED local MVP | Supervisor-approved System MVP; frontend does not know about FLUX, and the API delegates generation to the engine boundary. No deployment or real model integration is implied. |
| Temporary Kaggle GPU inference service for the first real-model demo, reached by the local FastAPI `RemoteFluxEngine` through a session tunnel | CONFIRMED | Implementation and local contract tests VERIFIED; live Kaggle and public endpoint NEEDS VERIFICATION | Supervisor's 2026-09-24 instruction. Base plus the project-trained TRAIN-001 LoRA stays loaded once per Kaggle session. A private Kaggle Dataset stores the adapter; the public Base snapshot is fetched into ephemeral scratch. Cloudflare Quick Tunnel is a testable temporary exposure mechanism, not permanent deployment. |
| DATA-001 V1/global FLUX.2 Klein Base editing for all 30 selected identities; masked V2 optional fallback | CONFIRMED | 30-image generation, sidecar integrity, and automated pair QA VERIFIED; final sheets show visual quality concerns | Supervisor's critical-path direction supersedes the earlier strict pilot/V2 prerequisite. The practical review standard accepts minor hair-color, lighting, clothing-detail, and accessory drift. Only a wrong hairstyle, major identity drift, severe artifacts, or major scene/pose change warrants one bounded retry. No output is auto-accepted. |
| One conditional Edit-LoRA for CrewCut, BobHair, and LayeredHair; evaluate at 250 steps and continue the same run toward 500 only if learning but underfit | CONFIRMED | Real 250-step run VERIFIED; held-out evaluation finds the checkpoint not visually cleared | Supervisor's model and training direction. The 250-step run preserved checkpoint and optimizer state. The Supervisor paused model-quality research and did not authorize 500 steps in this runtime task. |
| Preserve frozen TRAIN-001 as a fallback while assigning later hairstyle groups to separate LoRA adapters on the same FLUX.2 Klein Base | CONFIRMED | Registry and routing have local contract tests; multi-adapter Kaggle inference NEEDS VERIFICATION | Supervisor's controlled expansion direction. No TRAIN-002 checkpoint or style is active yet. |
| Add Makeup as a separate feature with a ten-style prototype catalog and isolated FLUX Base experiment | CONFIRMED | Application shell and local checks VERIFIED; Base makeup inference NEEDS VERIFICATION | Supervisor's MAKEUP-001 direction. The Base experiment has no adapter and makes no claim of trained Makeup support. MAKEUP-001 training, dataset construction, and live adapter integration are later stages. |
| Restrict MAKEUP-BASE-001 to three shared portraits and Natural Makeup, Soft Glam, and Smoky Glam, then stop for manual review | CONFIRMED | CPU planning and test checks VERIFIED; GPU inference and visual outcomes NEEDS VERIFICATION | Supervisor's pilot gate. No all ten run, face parser, DATA-M001, or MAKEUP-001 may follow merely from generated images. |
| Accept the reviewed three-style MAKEUP-BASE-001 pilot as sufficient to plan the next Makeup stage | CONFIRMED | Nine generated files and provenance VERIFIED; visual control remains EXPERIMENTAL with documented drift | Supervisor explicitly audited and approved the pilot on 2026-09-24. This advances planning, not a claim that identity preservation is solved, the three Pinterest images are licensed training data, or a Makeup LoRA exists. Training and live UI integration still require separate design and verification. |
| Scope the first MAKEUP-001 release to Natural Makeup, Soft Glam, and Smoky Glam with one isolated conditional Makeup LoRA | DEPRECATED | Superseded by Supervisor's 2026-09-25 DATA-M001 direction; model training NOT STARTED | The three looks were representative Base pilot styles, not the limit for MAKEUP-001. Keep the Makeup adapter separate from Hair. |
| Target approximately ten finalized Makeup styles in one conditional MAKEUP-001 LoRA | DEPRECATED | Superseded by the 2026-09-26 general Makeup edit decision; training NOT STARTED | The ten UI styles remain, but they are inference prompt presets rather than ten dataset training classes. |
| Require documented source rights, identity-separated data, and explicit visual review for DATA-M001 | CONFIRMED | Dataset source NOT SELECTED | Supervisor approved documented noncommercial academic use with attribution and change notices as needed. The three Pinterest pilot portraits remain research-only. If no suitable real pairs are available, reviewed synthetic counterparts from licensed source portraits are allowed. FFHQ-Makeup is a candidate only until its archive, labels, and item-level provenance are audited. |
| Gate live Makeup UI generation on held-out Base versus MAKEUP-001 evaluation | CONFIRMED | Evaluation NOT STARTED | The trained model must improve style control without worse identity drift before live UI wiring. The latest DATA-M001 split is two held-out validation identities, superseding the earlier four-identity working concept. This gives 20 initial style comparisons but cannot establish population-level generalization. Exact quality thresholds remain unconfirmed. |
| Audit FFHQ-Makeup before choosing DATA-M001 construction strategy | CONFIRMED | Pinned ZIP integrity and 12-identity visual sample VERIFIED; full style coverage and rights NEED VERIFICATION | Supervisor's 2026-09-25 DATA-M001 direction prioritizes this source but forbids training until design review. All five numeric variants are visually variable across sampled identities and cannot be treated as semantic classes. See [DATA-M001](../docs/data/DATA-M001.md). |
| Use selected FFHQ-Makeup bare portraits with ten controlled project-labelled targets per identity | DEPRECATED | Synthetic target visual gate FAILED; superseded by reviewed real FFHQ pairs | The earlier 100/20 artificial style target is closed. The actual DATA-M001 now contains 50/10 bare to existing makeup pairs, with numeric suffixes kept as positions only. |
| Stop DATA-M001 expansion after the first 20-target visual review and use Makeup-only preservation | CONFIRMED | 20/20 Base generations and provenance VERIFIED; CPU preservation processed 20/20 with exact parser-defined protected pixels VERIFIED; visual target suitability NOT VERIFIED | The Supervisor directed original-geometry Makeup appearance transfer and forbade further generation or training until review. Source-aligned transfer visibly improves identity and scene preservation but weakens subtle styles; no official human ACCEPT review is recorded. The remaining 100 stay stopped. |
| Do not freeze Preservation V3 or expand DATA-M001 yet | CONFIRMED | CPU V3 processed 20/20; pixel invariants VERIFIED; visual gate FAILED | Codex four-way review found six plausible candidates, three raw replacements and eleven systematic preservation failures. Regional median color loses spatially localized makeup and open-mouth lipstick remains uniform. No official training-pair ACCEPT decision exists. The next work remains a focused transfer correction on these 20, not a dataset search, model redesign or training run. |
| Do not freeze Preservation V4 or expand DATA-M001 after the final targeted correction | CONFIRMED | CPU V4 processed 20/20; pixel invariants VERIFIED; visual gate FAILED | Codex five-way review found three plausible candidates, three raw replacements and fourteen preservation failures, below the Supervisor's 16 to 18 usable-target gate. Spatial raw-minus-source appearance is contaminated by FLUX facial reconstruction even after semantic alignment and bounded transfer. No official training-pair ACCEPT decision exists. Keep the remaining 100 and MAKEUP-001 training stopped pending project-lead direction on this concrete blocker. |
| Test source-anchored FLUX.2 Klein Base inpainting before expanding DATA-M001 | CONFIRMED | Kaggle 4B/T4 load and 8/8 generations VERIFIED; visual style suitability FAILED | Supervisor directed a gated two-identity by four-style pilot with original portraits and parser-derived soft makeup masks. The pinned inpaint class loaded on T4 with no LoRA and eight images were reviewed; technical success did not establish usable style-separated targets. No Hair changes, remaining dataset generation, or MAKEUP-001 training followed. See [inpaint review](../docs/experiments/DATA-M001-inpaint-pilot.md). |
| Do not expand DATA-M001 from the first source-anchored inpaint run | CONFIRMED | Pinned 4B/T4 load and 8/8 generations VERIFIED; visual style-control gate FAILED | The eight-image visual review found improved apparent identity/scene retention but Natural, Soft, and Smoky virtually indistinguishable on both identities. One Red Lip candidate is plausible; the smiling lip has a heavy boundary. The current mask/strength/prompt combination cannot supply distinct four-style targets, so keep the remaining 100 and MAKEUP-001 stopped. See [inpaint review](../docs/experiments/DATA-M001-inpaint-pilot.md). |
| Test one targeted inpaint mask correction on the same eight cells | CONFIRMED | V1 double attenuation, V2 CPU masks, pinned T4 load and 8/8 generation VERIFIED; V2 visual style-control gate FAILED | The Supervisor authorized fixing the failed pilot. V2 normalized the V4 fields, strengthened source-constrained eye/cheek masks, and feathered the red lip while retaining prompts and inference settings. Review found a softer smiling Red Lip boundary but Natural, Soft and Smoky remain weak or poorly separated, with pale/silver Soft eye pigment in one identity. Do not expand DATA-M001 or train MAKEUP-001 from 8/8 technical success. See [inpaint V2 review](../docs/experiments/DATA-M001-inpaint-pilot.md). |
| Use global FLUX Base editing as the final DATA-M001 target method and run one bounded prompt refinement on the same 20 cells | DEPRECATED | V2 20/20 technical generation VERIFIED; visual training-target gate FAILED | The Project Lead closed this synthetic target path on 2026-09-26. The old 20 remain research evidence only; none enters the new real paired DATA-M001. See [global V2 review](../docs/experiments/DATA-M001-global-v2-review.md). |
| Train one general MAKEUP-001 edit LoRA on reviewed real FFHQ-Makeup bare to makeup pairs; keep ten styles as inference presets | CONFIRMED | DATA-M001 50/10 finalization, Project Lead's 60-pair contact-sheet approval, hashes and split VERIFIED; Kaggle training NOT STARTED | Supervisor's 2026-09-26 direction supersedes artificial ten-class targets. The selected real pairs are not reverse paired and numeric suffixes are not semantic labels. Use the stable 250-step T4 BF16 foundation, evaluate Base versus MAKEUP-001 on two held-out identities and all ten prompt presets, then wire the UI only if usable. See [DATA-M001](../docs/data/DATA-M001.md) and [MAKEUP-001 plan](../docs/experiments/MAKEUP-001-plan.md). |
| DATA-002 Philippine-priority ten-class source selection and balanced two-neighbor pairing graph | CONFIRMED | The Supervisor chose `Perm` instead of `SpikyHair`; 120 selected original photos decode and have unique hashes. The Kaggle generation run reported exit code 0 and 120 output PNGs; artifact integrity is not yet audited. | The frozen manifest SHA-256 is `25a3200c9a79be85ce19f690ba81f564d57d55d86d36e6383b0cacd1188ec5ab`. The `Perm` photographs support the visual label Perm-Style Curls, not a verified chemical treatment. The other nine identity selections are unchanged. Prior selections remain in Git history. |
| DATA-002 automated structural acceptance without exhaustive human visual review | CONFIRMED | Implementation and local fixture test pass; real Kaggle artifacts NEEDS VERIFICATION | The Supervisor explicitly authorized this deadline fast path for DATA-002 only. It must record `review_mode: automated_unreviewed`, preserve exact exclusions, and must not claim human review or model quality. DATA-001 and TRAIN-001 remain frozen. |
| Build a separate Nails feature on the shared FLUX.2 Klein Base foundation with one planned NAILS-001 edit LoRA, five prototype styles, nail-only final compositing, and identity-separated reviewed DATA-N001 | CONFIRMED | Prototype shell, geometry, offline segmentation and 100 reviewed real-source pairs VERIFIED; the step-25 adapter and held-out artifacts VERIFIED but five-style model quality FAILED; app inference NOT STARTED | Supervisor's 2026-09-26 Nails direction. Existing Hair and Makeup artifacts remain untouched. The experimental checkpoint is not approved for app inference; see [visual review](../docs/experiments/NAILS-001-step025-visual-review.md). |
| Run one controlled NAILS-001-LOCAL-v1 retraining attempt on fingertip crops from approved DATA-N001 | CONFIRMED | Localized 430-pair derivation and 20-sheet crop review VERIFIED; step-50 T4 training/artifact QA VERIFIED; five-style model quality FAILED, experiment PARTIAL | Supervisor's 2026-09-27 instruction authorizes fresh localized FLUX.2 Klein edit-LoRA training, frozen 16/4 identity split, exact exposure trace and held-out review. The step-50 adapter improves raw crop preservation but fails French Tip, Nude Pink and consistent Ombre on four unseen identities. Do not connect it to the app or overwrite step-25. One bounded continuation is a recommendation, contingent on verifying exact optimizer/checkpoint resume in the pinned toolkit; it is not yet run. See [step-50 evaluation](../docs/experiments/NAILS-001-LOCAL-v1-step050-evaluation.md). |
| Freeze Nails training and route five styles through a hybrid try-on pipeline | CONFIRMED | Local renderer/API integration and immutable step-50 runtime bundle VERIFIED; live GPU and full five-style browser run NEEDS VERIFICATION | Supervisor's 2026-09-27 decision supersedes the earlier no-app-connection and continuation recommendation for this phase. Classic Red and Glossy Black select the step-50 NAILS-001-LOCAL-v1 LoRA; Nude Pink, French Tip and Pink Ombre select the shared deterministic DATA-N001 renderer. All final pixels are restricted by the original nail masks. Hair and Makeup remain separate. See [integration](../docs/experiments/NAILS-001-hybrid-integration.md). |
| Correct Nails final plate geometry with source-resolution fingertip ROI segmentation while preserving hybrid routing and material | CONFIRMED | Production code, two-hand CPU visual/metric check and 112 backend tests VERIFIED; broad hand coverage and live Red/Black full-hand quality NEEDS VERIFICATION | Supervisor's 2026-09-27 authorization. The existing YOLO checkpoint and coarse 512 crop path remain; the final alpha now uses a conservative original-resolution ROI raster blend. No model or renderer material/training change was authorized. See [geometry results](../docs/experiments/nails-highres-geometry-2026-09-27/RESULTS.md). |
| Accept the two held-out MAKEUP-001 comparison sheets for practical app integration | CONFIRMED | Training and 40 evaluation output hashes VERIFIED; Project Lead visual approval recorded; preservation/generalization EXPERIMENTAL | On 2026-09-26 the Project Lead reviewed Original / Base / MAKEUP-001 for both identities and stated the rightmost outputs were consistently good. Proceed with the existing isolated Makeup integration direction. This practical gate does not prove unchanged geometry or fully subtle Natural/No-Makeup behavior. See [MAKEUP-001 evaluation](../docs/experiments/MAKEUP-001-evaluation.md). |
| SDXL Inpainting + trained LoRA + BiSeNet parsing + adaptive mask + IP-Adapter | DEPRECATED | UNKNOWN | Superseded by the more direct FLUX editing direction with fewer critical components. |
| FLUX.2 Klein + trained LoRA, paid FLUX.2 Pro API refinement, RunPod GPU | DEPRECATED | UNKNOWN | Superseded when Supervisor selected the $0 direction. |

Do not restore a deprecated architecture or silently change the confirmed one. Gather evidence and seek Supervisor approval for a new major decision.

## Deployment 01 decisions, 2026-09-28

Later startup automation: **CONFIRMED scope; LOCAL VERIFIED implementation; fresh-session NEEDS VERIFICATION.** Supervisor delegates a small publish/discover mechanism and authorizes additive START/STOP automation. Choose anonymous ntfy cached HTTP metadata with separately derived HMAC topic/signature, four-hour expiry and latest-only selection, then verify public/authenticated worker identity. No API key published, no local URL cache, `.env` write, silent rollback or generation retry. Public support scripts are pinned to a Git commit/hash; the private Deployment-01 package remains unchanged. Mailbox failure is explicit and permits a verified manual override; it is a demo dependency, not persistent hosting. Owned Windows jobs/controller prevent arbitrary process kills. [Decision](../docs/specs/0002-capstone-startup.md), [guide](../docs/guides/capstone-start.md).

| Decision | Status | Evidence | Rationale and authority |
| --- | --- | --- | --- |
| Preserve single-attempt remote generation; add correlation/crop diagnostics and manual history checks rather than automatic retry | CONFIRMED | Source audit: no prior retry/deduplication; timeout/disconnect acceptance is ambiguous. Focused diagnostics and ownership regressions LOCAL VERIFIED; original 502 cause UNKNOWN | Supervisor's conservative Deployment-01 instruction. Zero automatic retries, including 429. Missing bounded history never proves non-acceptance; ownership remains held until GPU work drains. |
| Reuse approved unified notebook/bootstrap/assets for repeatable demo startup, with image-free readiness and a bounded fresh-session rehearsal | CONFIRMED | New private bundle/notebook preflight and 299 backend tests LOCAL VERIFIED; fresh Kaggle rehearsal NOT STARTED | Supervisor authorizes capstone preparation, not permanent hosting. Include existing approved latency support without changing chosen settings; preserve separate services and legacy routes. `CAPSTONE_DEPLOYMENT_READY` requires returned fresh-session evidence review. [Runbook](../docs/guides/capstone-deployment01.md). |

## Application integration decisions, 2026-09-27

| Decision | Status | Evidence | Rationale and authority |
| --- | --- | --- | --- |
| Evaluate one private FLUX GPU worker with a single Base load and serialized adapter switching after the application integration | PROPOSED | Cross-feature GPU sharing NEEDS VERIFICATION | [Earlier architecture proposal](../docs/specs/0001-shared-application-architecture.md). The Supervisor explicitly deferred shared GPU loading from phase 1. Separate Kaggle services remain the confirmed current arrangement; further approval and tests are required before changing them. |
| Retain Kaggle as the remote GPU provider for the upcoming central architecture integration, behind configurable inference clients | CONFIRMED | Separate Kaggle server scripts, bootstrap guides and backend URL/key configuration VERIFIED IN SOURCE; permanent service availability UNKNOWN | Supervisor's 2026-09-27 preservation instruction. Do not migrate providers or redesign the Kaggle runtime in the baseline task. Future GPU provider replacement should not require frontend or feature pipeline redesign. |
| Add central application feature discovery and dispatch while retaining legacy routes and three separate Kaggle runtimes | CONFIRMED | New `/features` endpoints and registry locally verified; live Kaggle through new routes NEEDS VERIFICATION | Supervisor's 2026-09-27 integration instruction authorizes an additive `hairstyle`/`makeup`/`nails` application contract. Existing feature handlers remain the source of style validation, processing and errors. Shared GPU loading and adapter switching are deferred. |
| Migrate all three pages through the existing shared frontend API client to central feature routes; keep separate UIs and no automatic legacy fallback | CONFIRMED | 24 frontend tests, lint/build and 122 backend tests VERIFIED; live Kaggle through migrated frontend NEEDS VERIFICATION | Supervisor's Phase 2 direction. Reuse `NEXT_PUBLIC_API_BASE_URL`, retain Hair health labeling and feature presentation metadata, and preserve the existing backend pipelines and separate GPU runtimes. |
| Close central application architecture with local/mocked/browser evidence while deferring live GPU validation | CONFIRMED | 152 backend tests, 28 standard frontend tests, 8 synthetic remote client/Edge checks and lint/build VERIFIED; live centralized AI inference NOT VERIFIED | Supervisor's Phase 3 direction. Keep actual feature handlers, clients and Nails hybrid processing; fake only remote HTTP and vision boundaries. Fix malformed-response normalization only. Kaggle stays the intended provider, runtimes stay separate, legacy routes stay available; no notebook activity, model change or GPU consolidation. |
| Audit one Kaggle runtime without changing working services or starting full implementation | CONFIRMED | Runtime source, requirements, checkpoint layout and historical measurements inspected; no live experiment | Supervisor's later feasibility-only instruction. Central architecture and separate services remain the working fallback; this audit is not implementation approval. |
| Use one pinned CPU offloaded Base with serialized feature adapter unload/load in the unified Kaggle runtime | CONFIRMED | Gate 1 individual equivalence, Gate 2 persistent switching/recovery and Gate 3 live one-URL application integration VERIFIED | Supervisor authorized the incremental Gate 3 integration. The backend keeps its feature clients and local Nails hybrid work; the separate GPU services remain rollback. This is capstone/demo acceptance, not durable public deployment. [Gate 3 review](../docs/experiments/unified-kaggle-gate3-live-review-20260928.json). |
| Prepare Gate 1 on the evaluated Nails dependency stack with fresh sequential pipelines and historical fixed references | CONFIRMED | Harness/artifact preflight and 39 focused tests VERIFIED locally; three individual GPU outputs and exact fixed-reference equivalence VERIFIED after returned evidence review; GATE_1_PASSED | Supervisor's 2026-09-28 instruction authorizes this isolated experiment only. Original runtimes, weights, settings and application configuration preserved. Reviewed resources show no blocker to a next experiment; unused Kaggle package conflicts and historical visual limits remain. Acceptance is for individual cases only, not shared switching/server, all-style quality or central live validation. Gate 2 requires separate authorization. [Evidence and limits](../docs/experiments/unified-kaggle-gate1.md). |
| Gate 2 with one persistent foundation, normal single adapter unload/load and exact observed Gate 1 environment | CONFIRMED | Preparation: 40 new plus 39 retained tests LOCAL VERIFIED. Returned GPU evidence independently reviewed: GATE_2_PASSED for approved fixed cases, restoration/serialization and bounded memory observations | Supervisor authorizes Gate 2 only. One foundation, all 17 exact PNG/RGB matches, verified active adapters and five blocked/restored failure probes; concurrency/repeated cancellation preserve ownership. No observed progressive memory blocker. Actual CUDA OOM/HTTP disconnects, all styles and long-run serving remain unverified. Original methods/settings/weights, existing services and Gate 1 evidence unchanged. No production server/application migration or Gate 3; recommend separate authorization for candidate server/service acceptance. [Reviewed evidence and limits](../docs/experiments/unified-kaggle-gate2.md). |
| Implement Gate 3 as an additive one-foundation Kaggle HTTP candidate with one shared backend URL/key | CONFIRMED | GATE_3_PASSED: returned Kaggle archive, exact Gate 2 environment, one Base, live central browser Hair → Makeup → Nails → Hair, renderer bypass and safe HTTP probes independently VERIFIED | Supervisor's Gate 3 authorization. Use Gate 2 owner and original generation methods, one Uvicorn worker, feature-aware routes and the existing clients. Keep the three original servers, URLs/keys, legacy routes, pages and Nails local hybrid stages. Unified configuration is explicit and reversible; one session/URL now serves live Hair, Makeup and Nails plus renderer-only path. The observed Nails transport 502 recovered on retry; durable availability remains unverified. [Experiment](../docs/experiments/unified-kaggle-gate3.md). |
| Allow neighboring nail context when original isolated crop search cannot fit a valid visible nail | CONFIRMED | Exact reported input and preservation regressions LOCAL VERIFIED; corrected input LIVE VERIFIED through central API and unified GPU, five nails, zero changes outside final mask | Supervisor explicitly requested fixing excessive rejection. Keep original successful mappings unchanged; select the least neighboring context within existing crop sizes for rejected close poses. Existing selected nail and final mask compositing remains the output boundary. No skipped fingers, renderer substitution, model change or retraining. [Correction evidence](../docs/experiments/nails-close-pose-crop-fix-20260928.md). |

## Automatic Render/Kaggle endpoint registration, 2026-10-10

**CONFIRMED.** Supervisor approved the source-grounded Neon registration proposal with “okay lets proceed”. Render retains existing authentication and AI routing; Kaggle announces the protected CPU facade URL with a domain-separated signature derived from the existing backend key. One additive operational metadata table persists a 180-second lease, renewed every 60 seconds while the session processes/ports are alive. Newer sessions replace only expired leases; old sessions/replays cannot reactivate their address. Static mode is explicit rollback, never automatic stale fallback. No additional hosting service, model change or retraining. [Contract](../docs/specs/0009-automatic-kaggle-registration.md).


## Client business improvements planning, 2026-10-17

**CONFIRMED scope clarification:** Supervisor wants daily completed services and recorded amounts, not payment accounting, and requests planning the missing Makeup booking option. **PROPOSED, not approved for implementation:** saved-look storage/retention, appointment linkage, service-day reporting and UI/API/schema changes in [the review plan](../docs/specs/0010-saved-looks-booking-daily-services.md). No migration, code implementation or deployment authorization inferred from planning.

## Saved-look business workflow implementation approval, 2026-10-17

**CONFIRMED:** Supervisor's “proceed on development” approves the reviewed web implementation. Reuse existing Neon generations/appointments, persist generated previews with bounded quotas, preserve booked references on gallery removal, allow one selected look per appointment, and report completed-service recorded amounts by scheduled Asia/Manila service day. Initial Makeup Application remains Price to be confirmed; business label and real storage/device gates are checked before release. Development is locally verified; the plan's separate production migration/deployment approval remains in force. No payment ledger, GPU/model changes or native Save/Book screens are included. [Current guide](../docs/guides/saved-looks-booking-rollout.md).

## Saved-look production rollout authorization, 2026-10-17

**CONFIRMED:** Supervisor said “lets try that now” to the explicit recovery-point → migration → Render deployment → feature enablement → live testing sequence. This supersedes the pending deployment authorization above. Existing Kaggle notebook/models remain unchanged. An automatic-review rejection prevents an unapproved local export of live account/client records; use a provider-side Neon recovery branch. Render dashboard actions require the user in this session because browser-control tools and management credentials are absent. [Progress evidence](../docs/experiments/saved-looks-render-rollout-20261017.json).

## Supervisor waives new rollout backup, 2026-10-17

**CONFIRMED:** In direct response to the provider-side recovery-branch request, Supervisor said “lets skip that”. Proceed with the authorized additive production migration without creating a new backup; do not reinterpret this as permission to export live client/account rows locally. Both migration batches subsequently applied and record preservation was verified via server-side aggregate checksums. Existing schema additions/data are retained on application rollback. Render manual deployment and live rehearsal remain. [Evidence](../docs/experiments/saved-looks-render-rollout-20261017.json).

## New improvements review boundary, 2026-10-18

**CONFIRMED:** Supervisor requests code inspection/findings and a concise implementation plan before development for generation speed, catalog-grounded descriptions/costs and Market Trends removal. Explicitly **do not deploy this update to Render**. No implementation or new live schema/notebook changes inferred. **PROPOSED:** measure first, bounded fixed-prompt encoding reuse if justified, one saved metadata snapshot in existing generations, retain shared stats/history APIs while removing Trends page/navigation. Price mappings/missing prices and native display scope remain review items. [Plan](../docs/specs/0011-generation-speed-look-details-remove-trends.md).

## Generation improvements development approval, 2026-10-18

**CONFIRMED:** Supervisor “lets start” authorizes the reviewed local web-first implementation and isolated profiling/cache experiment; separate private Kaggle benchmark session confirmed available. Preserve model settings, working demo notebook/bundles, current live system and native payload compatibility. Explicit no-Render-deploy boundary remains; no live migration or cloud configuration change inferred. Named service estimates are conditional, unpriced Makeup/curl/wave services quote-required, historical saved snapshots immutable, legacy estimates labeled current. Cache remains experimental and disabled until actual paired GPU timing/quality and application review. [Implementation guide](../docs/guides/generation-improvements-local-review.md).

## Focused generation rehearsal authorization, 2026-10-18

**CONFIRMED:** Supervisor “proceed” follows the worker comparison's proposed full-hand/Consultation rehearsal. Prepare a separate private user-run Kaggle test with existing model parameters and immutable bundles, temporary local credentials, no public endpoint or website registration. Use existing deterministic recommendations to compare identical generated looks, clearly excluding Gemini conversation/browser acceptance. Preserve working demo, live database and no-Render-deploy boundary. Cache adoption remains pending returned application evidence; receipt/preparation of a test notebook does not enable it. [Guide](../docs/guides/application-rehearsal-20261018.md).

## Application cache scope recommendation after real evidence, 2026-10-18

**PROPOSED:** restrict future opt-in prompt reuse to model-based Nails, including Nails invoked by Consultation; preserve original Hair/Makeup paths and renderer behavior. The returned application artifact verifies exact preservation but shows new Hair/Makeup timing regressions alongside faster full-hand Red/Black. Therefore global cache activation does not satisfy the performance gate and remains disabled. This is an evidence-based next implementation recommendation, not a claim of a scoped patch, new user deployment approval or an enabled feature. The explicit no-Render-deploy boundary and current working fallback remain. [Review](../docs/experiments/application-rehearsal-20261018-review.md).

## Consultation workflow scope review, 2026-10-19

**CONFIRMED:** Supervisor requests inspection and a proposed plan only; do not implement, redesign, migrate or deploy. **PROPOSED:** reuse saved generation/appointment links and shared previews; controlled completion timestamp/actor; one verified appointment review; actual product/brand usage child records tied to completion and optional existing inventory; computed transparent counts/ratings. Keep existing completed-service recorded-amount reporting. Quantity/cost units and profit meaning require review; automatic stock deduction, full inventory/accounting, availability engine, realtime and native parity are outside the minimum. No proposal is implementation approval. [Review plan](../docs/specs/0012-consultation-booking-completion-reviews-products.md).

## Minimum workflow development approval, 2026-10-20

**CONFIRMED:** Supervisor “lets start” follows the completed audit/minimum implementation recommendation and authorizes local web development. Preserve the existing no-Render-deploy boundary and working Kaggle system; no live migration inferred. Implementation defaults preserve optional booking stylist (assignment required to complete), optional product/brand/quantity/unit/material cost, existing admin amount/notes correction and scheduled Manila reporting. One review per completed assigned appointment; no editing/reopening/reassignment after completion. Counts and rating sorts remain separate/explicit with review counts. No automated stock deduction, true-profit ledger, advanced availability, realtime or native expansion. Local verification does not authorize a production release. [Guide](../docs/guides/consultation-booking-workflow-testing.md).


## Combined release authorization, 2026-10-20

**CONFIRMED:** Supervisor explicitly says deploy on Render and Kaggle together with generation optimization; this supersedes the earlier no-deploy boundary for this release. Apply additive workflow migrations and publish existing verified web changes. Use only measured model-Nails prompt reuse, preserve baseline Hair/Makeup and original notebook/datasets/model parameters. User confirms no GPU session running. Schema-only verification is used after automatic review rejected optional local record-derived hash export; no new record-export permission inferred. Actual Render trigger/Kaggle startup require operator in absence of control credentials/runtime.


## Guest trial review boundary, 2026-10-20

**CONFIRMED:** Supervisor requests actual-code feasibility and a minimal plan before implementation, defers current-release testing, and requires existing registered consultation/limits preserved. No coding/migration/deployment/GPU action authorized by this request. **PROPOSED:** separate public one-selected-image consultation, narrow guest gateway and durable atomic Neon allowance, preserving member auth and Kaggle inference. One-admitted-attempt policy, trial window/budgets, signup image carryover and public anti-abuse exposure remain review items; no strict lifetime one-human promise. [Plan](../docs/specs/0013-guest-consultation-trial.md).


## Guest consultation development approval, 2026-10-20

**CONFIRMED:** Supervisor approves the recommendation with "lets start with your recommendation". Proceed with local development, preserving existing running Render/Kaggle and registered flow. Adopt configurable30-day browser allowance, one admitted attempt, conservative abuse limits, fresh full consultation after signup and flag OFF. No release/live schema/GPU authorization inferred. Exact guest-image carryover, CAPTCHA/person verification, new member quotas and priority queue remain outside this slice. Actual proxy configuration requires verification before later enablement. [Guide](../docs/guides/guest-consultation-trial.md).


## Guest trial production release authorized, 2026-10-20

**CONFIRMED authorization / IN PROGRESS.** Supervisor requests Render+Kaggle deployment. Additive0006 table/function applied to existing configured Neon and independently schema-only verified; no client/account/booking records exported or changed.24guest tests and production build/TypeScript pass. New availability probe returns only booleans for trusted-ingress verification, no auth/storage/inference. Kaggle active lease=false; operator asked to restart existing optimized notebook. No notebook/model/data/secret changes. Guest flag must stay off through web deployment/proxy test. GitHub publication being finalized; manual Render trigger/config requires operator because no supported control runtime/credentials.


## Guest limit feedback request, 2026-10-20

**CONFIRMED:** Supervisor requests a modal and contextual indicator when the guest generation allowance is used. Reuse current session/quota and account continuation; preserve completed image/download and member flow. This is a frontend correction in the authorized guest rollout; no new quota, migration, Kaggle restart or model scope. Modal distinguishes used allowance from processing/unresolved requests. [Evidence](../docs/experiments/guest-trial-limit-feedback-20261020.json).


## Style expansion research direction, 2026-10-25

**CONFIRMED:** Supervisor authorizes proceeding with staged expansion, then rejects generic initial examples and requests researched trendy Hair/Makeup/Nails options. Prepare a specific researched shortlist and isolated data/evaluation artifacts. **PROPOSED:** the13candidates in docs/specs/0014-style-expansion.md and pilot ordering; selection, salon mappings and actual generation quality are not approved/verified by trend evidence. Preserve current production IDs, reviewed model guards and demo fallback. No wholesale data scraping or production enablement from trend references.


## First style expansion pilot authorized, 2026-10-25

**CONFIRMED:** User requests proceeding based on the researched recommendation and confirms a separate Kaggle T4 session. Implement isolated feasibility tools for the recommended eight-style first batch; this authorizes testing, not a claim of model support or deployment. Existing training labels/adapter metadata, production Makeup hash guards, old public IDs and demo artifacts remain unchanged. Other five researched candidates remain PROPOSED. No new base model, architecture, public endpoint or automatic catalog promotion.


## MAKEUP-QA-001 authorized, 2026-10-25

**CONFIRMED:** Supervisor says proceed with the bounded complexion diagnostic, then confirms a fresh Kaggle notebook is needed. Test foundation-only/current/reduced adapter influence on2existing people and2existing presets, preserving original models/prompts and deployed systems.0.5is an experimental factor, not an approved live setting. No masking/compositing, failed old data-method revival, architecture replacement, training or production promotion authorized by these results alone.


## 2026-10-25 — Limited Makeup adjustment comparison

**CONFIRMED:** Supervisor says proceed with the proposed separate guidance and complexion/foundation prompt tests, then confirms the same completed diagnostic session remains running. Scope is experimental MAKEUP-QA-002 at adapter1.0/20steps/seed1977/512square, with prior controls and cached setup preserved. This authorizes preparing the9call comparison, not production parameter/prompt changes, training, masks, image blending/recoloring or deployment. Quality acceptance remains NEEDS VERIFICATION.


## 2026-10-25 — Guidance 2.5 follow-up

**CONFIRMED:** Supervisor prefers guidance3.0 relative to matched-foundation output and says proceed with the proposed3.0vs2.5comparison. Same session remains running. Scope is MAKEUP-QA-003:8retained4/3references, one3.0control plus4new2.5images, unchanged original prompts/adapter1.0/steps/seed/frame. This authorizes the bounded experiment, not automatic selection/deployment, training, new processing methods or a continuing guidance sweep.


## 2026-10-25 — Preferred Makeup output: guidance 2.5

**CONFIRMED:** Supervisor explicitly selects LATEST RESULT when asked2.5latestversus3.0after reporting visual improvement. Use2.5as selected candidate for a subsequently authorized rollout, retaining original prompts/full adapter and unchanged steps/seed/frame. This supersedes the earlier provisional3.0preference; no automatic deployment, contract alteration, new training or further parameter sweep follows. Live settings remain unchanged.


## 2026-10-25 — First expanded release validation/integration phase

**CONFIRMED:** Supervisor says proceed after the plan to validate selectedMakeup2.5,CommaHair and3Nailrenderers, integrate accepted entries then deploymatchingpackages withfallback. PriorGPUended; Supervisor explicitly requestsfreshnotebook. Prepareisolatedvalidation andlocalautomaticmaskchecks first; no publicstylepromotion beforeactualreview. Live rollout not started, oldartifacts retained. Versionedcompatiblecontracts are required; approval does not justify disabling ownership/hash checks or fabricating prices.


## 2026-10-25 — Berry Makeup quality rejected

**CONFIRMED:** Supervisor rejects suppliednewBerryoutput for whitening/unnaturalblend. Do not include it in expandedrelease or describe selected2.5as a complexionfix. Earlierrelative2.5preference is historical and not broadvisualacceptance. No authorization to disable liveMakeup, retrain or change architecture inferred. Targetreview/correctionplan precedes furtherGPUwork;Nails independent.


## Corrective data audit and replacement research authorized, 2026-10-25

**CONFIRMED:** Supervisor says proceed to the fix under the paired-target audit plan, then explicitly selects “Investigate replacement datasets” instead of salon photo collection. Scope covers immutable target review and primary-source replacement investigation. No external access inquiry has been sent, agreement accepted, replacement dataset selected for training, model architecture changed or live Makeup service disabled. **PROPOSED:** obtain reviewed paired samples and clarify applicable permissions before a bounded corrected-data trial. The zero-keep Codex screen is not fabricated human approval.


## Replacement-data access phase, 2026-10-25

**CONFIRMED:** Supervisor says “lets proceed” after the sample-access/review-first recommendation. Continue bounded noncommercial research intake and prepare provider inquiries, preserving existing models and artifacts. **No external message sent, agreement accepted, replacement source selected for training, or deployment performed.** Actual zero-image network-failed intake is recorded separately from prepared access request.


## Offline tone experiment authorized, 2026-10-25

**CONFIRMED:** Supervisor says “proceeed” to the bounded existing-photo skin-tone comparison proposal after clarifying that external training images are not required for an adjustment experiment. Scope is isolated CPU post-processing, exact original/raw preservation and appearance review. One implementation boundary defect was corrected without changing tone caps, model settings or case selection. No production integration, new training, architecture migration or deployment is inferred from this experiment. Actual results remain EXPERIMENTAL pending human review.


## Tone correction mask rejected, 2026-10-26

**CONFIRMED:** Supervisor rejects the shown MAKEUP-TONE-001 v2 Natural054109 output for a visible mask/poor blending. Supersedes its pending human acceptance for this case; preserve original output and prior partial-improvement observations as history. Do not promote this prototype, infer approval for other cases, or treat32technical checks as appearance acceptance. No automatic retraining or architecture replacement authorized by this feedback.


## AI-assisted cosmetic rendering acceptable, 2026-10-26

**CONFIRMED:** In response to whether Makeup must come from the trained generative model, Supervisor selects “AI-assisted cosmetic rendering is acceptable.” A source-based AI-region/custom-cosmetic rendering method is therefore acceptable in principle. This does not make unimplemented rendering successful, approve misleading trained-adapter labels, or authorize claiming all existing styles are supported. **PROPOSED:** bounded3style/4photo visual pilot before integration and coordinated deployment, as documented in the recovery plan. Preserve trained model/history and accurate method reporting.


## Source-based rendering pilot authorized, 2026-10-26

**CONFIRMED:** Supervisor says “proceeds” after the plan for a12preview source-based AI-assisted Makeup pilot. Implemented only this isolated pilot; one pigment gamut defect corrected with fixed sources/regions/opacities. No production/catalog/profile promotion or cloud rollout follows automatically. Appearance acceptance is pending; trained generative Makeup and render-only mode must remain accurately distinguished.


## Seven remaining existing Makeup styles authorized, 2026-10-26

**CONFIRMED:** Supervisor says “proceed to your plan” after the remaining7existingstyles and separate3expansioncandidates were explained. Proceed with28offlinepreview extension and honest feature limits. This authorizes implementation/evaluation, not recording blanket human appearance acceptance or live deployment. No-Makeup/Smoky/Dewy/Rosy/Bronze/Matte/Evening now have experimental source-renderer profiles; futurefull-facefinish/lashclaims and styleavailability need explicit resolution.


## Makeup insufficiently visible beyond lips, 2026-10-26

**CONFIRMED feedback:** Supervisor says source-renderer examples do not sufficiently look like makeup; lips are the noticeable change. This is not approval of all10profiles/deployment. Goal remains visible eye/cheek cosmetics without whitening/full-face reconstruction. MAKEUP-VISIBILITY-001 is a bounded implementation response; client acceptance pending. No new external-data/training/cloud decision.


## Makeup visibility comparison not accepted, 2026-10-27

**CONFIRMED user feedback:** latest source-rendered comparison still does not look sufficiently made up. MAKEUP-VISIBILITY-001 is not accepted as a solution; no per-case judgments inferred. Historical70technicalchecks/12exactreproductions do not prove appearance quality. Inspected current code implements localized pigment/darkening/finish; brows remain protected, full lash/foundation/contour capability is absent. Missing components are verified; their causal contribution to this rejection is not.

**PROPOSED / NOT STARTED:** stop opacity-only sweeps. Establish an explicit visual target, ideally a user reference, then one complete Soft Glam prototype with shaped lid shading, defined lash line and coordinated cheek/lip effects. Brow/lash details require deliberate anatomy/protection review, not drawing over protected regions blindly. Preserve source complexion/identity. Validate a small comparison before all-style expansion or versioned integration. No new images, rendering code, dependencies, inference, training or cloud changes this turn. Current output is not release-ready. [Rejection](../docs/experiments/makeup-visibility-rejection-20261027.json).


## Makeup visual target supplied, 2026-10-27

**CONFIRMED:** Supervisor supplies a portrait as the approximate desired makeup appearance/strength. Warm rose-bronze lids, prominent lashes/brows, rosy blush, localized glow and glossy rose-brown lips are the implementation interpretation of visible elements, not exact product/color specifications. No complexion/identity copy or studio-light replication requirement inferred. Previous rejected previews are not approved. One complete-look test remains visually rejected by Codex; no new architecture/deployment decision.


## Bounded Makeup alignment work authorized, 2026-10-30

**CONFIRMED:** User says proceed to the proposed local alignment check and one Soft Glam correction on four existing photos, with method reassessment if still artificial. No approval of failed outputs, ten-style rollout or cloud deployment. Result fails Codex visual screen. Dedicated pretrained reference-conditioned Makeup is now PROPOSED for isolated feasibility review, not an approved/implemented production replacement.


## Deadline and free-only Makeup triage, 2026-10-30

**CONFIRMED constraints:** Supervisor's demo is within24hours; keep everything free. Paid image API route ruled out, no paid calls authorized/made. ExistingGemini integration verified TEXT ONLY; currenttrained Makeup response contract cannot become an image API by changing the text model name.

**PROPOSED:** stop custom-lash/strength sweeps and training; one time-boxed isolated Kaggle pretrained reference-transfer trial after asset/dependency preflight. Official Stable-Makeup public folder visibly lists3expectedcheckpoint names; full downloads/auxiliary assets/terms/runtime/T4fit/appearance still unverified. Do not spend GPUquota until completepreflight. If it cannot pass quickly, freeze scope and present Makeup's limitation honestly; labeledreferenceexamples cannot masquerade as live clientgeneration. No newnotebook/runtime/provider/cloud change yet. [Triage](../docs/experiments/makeup-deadline-triage-20261030.json).


## One free pretrained Makeup trial authorized, 2026-10-30

**CONFIRMED:** Supervisor says proceed after the isolated four-photo/reference pretrained-model trial is explained. Authorizes preparation and that evaluation, not a production architecture/model replacement, paid API, new training or all-style rollout. Budget free, demo within24hours. No appearance approval inferred. Artifacts ready; actualKaggletrial remains next.


## Supervisor resets Makeup scope to original white-cast problem, 2026-10-30

**CONFIRMED correction and human rejection:** Supervisor says latest result looks worse and asks why work drifted from initial whiteness issue. Original goal remains reducing excessive pale/white skin in existing BeautyCore Makeup while retaining visible cosmetics and the same person. Codex acknowledges scope drift into replacement rendering/full-face reference generation. STABLE-MAKEUP-001 is now explicitly human-rejected, not only a Codex rejection.

Stop the replacement/full-look expansion branch under the current task. Return to original deployed pipeline and accumulated diagnostic evidence before proposing a targeted white-cast correction. Do not restart GPU/parameter/model/training sweeps or deploy rejected candidates. Earlier skin-only MAKEUP-TONE-001 correction also failed with a visible mask; it is not a valid accepted fallback. No accepted fix exists yet, and no promise of a safe single-setting solution is justified. No code/images/GPU/deployment change in this reset. [Scope reset](../docs/experiments/makeup-scope-reset-20261030.json).


## Full expansion target selected; release remains gated, 2026-10-30

**CONFIRMED scope:** Supervisor wants all proposed Hair, Nails and Makeup expansion styles considered for use, with Makeup tested before rollout. This selects the target scope; it does not establish that previously failed or untested styles work or approve rejected appearances. Existing catalogs remain intact. **IN PROGRESS / NEEDS VERIFICATION:** complete per-style validation, compatible production catalog/consultation/renderer/model-profile integration, actual service-price mapping, save/book regressions, matching versioned Kaggle packages and application rehearsal. Makeup remains on the original white-cast correction scope. No blanket production enablement, new training or replacement-model adoption is inferred. Current expanded release is not deployment-ready; no production changes made by this clarification.


## Expanded styles implementation authorized, 2026-10-30

**CONFIRMED:** Supervisor says proceed after the versioned release architecture and first development milestone are presented. Implement release compatibility and three tested Nails integrations while preserving visual acceptance gates and current deployment. Subsequent response says they need to review images first; do not mark the three designs accepted or enable them. No new cloud rollout, replacement Makeup model or training decision is inferred.


## Three reviewed Nail designs approved, 2026-10-30

**CONFIRMED:** Supervisor says "I approve the design it looks good" after the repaired four-hand gallery. Accept Raspberry Jelly, Pink Aura Ombré and Negative-Space Micro-Dots only. This supersedes their pending visual review. Enable those installed profiles in the local release and prepare matching artifacts; it does not approve Hair/Makeup or the other two Nail finishes, nor establish cloud readiness. Existing original Makeup correction scope and free-only constraints remain. [Approval record](../docs/experiments/expanded-nails-approval-20261030.json).


## Hair expansion validation resumed, 2026-10-30

**CONFIRMED:** Supervisor requests proceeding to haircut after Nail approval. Continue the already approved gated release plan with a Hair-only comparison on suitable existing inputs. This does not accept held Comma/Butterfly/Two-Block outputs or enable untested Wolf/French Bob. No new architecture, model training, paid provider or cloud rollout is inferred. Prepared21fixedcalls with original adapters/settings, then per-style visual review before production profiles. Original Makeup correction remains separate.


## French Bob appearance approved, 2026-10-31

**CONFIRMED:** Supervisor says "i APPROVE IT" after the preceding response identified French Bob as the strongest candidate for review and explicitly held the other four Hair styles. Apply approval to French Bob only, including its actual curly interpretation and disclosed hair-color limitation. Continue the already approved production-profile/release plan. This is not approval of Butterfly/Wolf/Two-Block/Comma, a fix for recoloring, retraining or new cloud expenditure. [Approval](../docs/experiments/french-bob-approval-20261031.json).


## All expanded Hair and Nail designs approved, 2026-10-31

**CONFIRMED:** Supervisor says "i approve all of the expanded haircut and nails. then lets see the makeup now." This supersedes the French-only interpretation and quality-based holds for the four other reviewed Hair outputs. All five Hair appearances are accepted as shown, with known shape/color limits retained. All five Nail designs are approved scope; only three have reviewed/generated implementations, and Pearl Chrome/Cat-Eye still require implementation/testing. Do not fabricate unseen results or bypass runtime profile integrity. Remaining routes/finishes go into a new release; preserve existing immutable packages while focusing next on Makeup. No Makeup approval or white-cast fix is implied. [Approval](../docs/experiments/all-hair-nails-approval-20261031.json).


## Deploy approved Hair/Nail expansion before Makeup, 2026-10-31

**CONFIRMED:** Supervisor requests deploying Hair and Nails first while Makeup is fixed separately. They explicitly choose: "Integrate all five approved haircuts first, then deploy with the three tested Nail designs." This authorizes the five reviewed Hair production profiles and three tested Nail renderers, scoped publication and rollout. Keep existing Makeup settings/functionality, hold all new Makeup additions, and leave unbuilt Pearl Chrome/Cat-Eye out. No retraining, new paid provider, database migration or blanket approval of Makeup is inferred.


## Original Makeup skin-tone blending reaffirmed, 2026-11-01

**CONFIRMED:** Supervisor resumes Makeup and explicitly wants cosmetics to blend with the person's skin tone, rather than more offered styles or a replacement full-look method. Existing free-only and preservation constraints remain. The current work is a bounded offline correction using existing saved inputs/results, not an adopted new production architecture/model, accepted appearance or deployment approval. No new human acceptance is inferred from the request.


## Subtle original-photo retouch priority, 2026-11-01

**Superseded interpretation / later human rejection:** Source-only subtlety removed the required makeup. Preserve original person AND selected makeup together; see the latest correction below.

**CONFIRMED:** Supervisor says skin-tone blending is better but the result is too regenerated/far from original. They explicitly request subtle complexion correction, source facial features/shape/expression/texture/imperfections/lighting/background/hair preserved, no overly perfect cosmetic details. This authorizes an offline source-primary refinement and supersedes stronger-makeover visibility as the priority for this specific prototype. It is not whole-image approval of MAKEUP-COMPLEXION-001, adoption of older rejected rendering/lash methods, or permission to silently replace every existing Makeup style in production.

## Preserve makeup and original person together, 2026-11-01

**CONFIRMED:** User rejects the source-only retouch because it removed desired cosmetics. Earlier wording that source subtlety superseded cosmetic visibility was an assistant misinterpretation and is **DEPRECATED**. User requires selected eyeshadow, liner, lashes, blush and lipstick style/intensity/color intact while complexion blends and original identity/texture/geometry/lighting/scene remain.

User answers all to the three offered reference choices: Natural Makeup, Cloud/Berry Lips and Classic Red Lip. This authorizes checking those references together; no successful all-catalog implementation, replacement model, new training or production adoption is inferred. Offline cosmetic-layer v1/v2/v3 fail Codex visual review; none is adopted. [Evidence](../docs/experiments/makeup-selected-cosmetics-20261101.md).

## Cosmetic separation repair authorized, 2026-11-01

**CONFIRMED:** User asks to plan the fix and proceed. This authorizes the targeted offline separation repair and verification while preserving original person and selected makeup together. It does not approve a weaker generic look or production replacement. Three selected references on two reused people remain the bounded matrix. Final v2.1 is a partial candidate; source-protection/technical passes do not establish cosmetic intensity fidelity. No new user appearance acceptance or deployment is inferred. [Evidence](../docs/experiments/makeup-separation-20261101.md).

## Selected cosmetics must be visibly recognizable, 2026-11-01

**CONFIRMED:** User reviews the prior result as too subtle. They request closer selected color, intensity and placement with original identity/geometry/texture/light/hair/scene preserved and no harsh or overly dramatic makeup. This refines the same standing requirement. It does not authorize a generic palette, lower visibility as a fallback, replacement person or deployment. Latest local reference-application candidate is not human-approved. Lipstick is intentionally not intensified because it was already prominent. [Evidence](../docs/experiments/makeup-reference-visibility-20261101.md).


## Original canvas and natural cosmetic boundaries required, 2026-11-02

**CONFIRMED:** User explicitly rejects current pasted cosmetics and regenerated appearance. Original photo is the face canvas; selected makeup guides only cosmetic style/color/placement. Preserve source eyebrows, geometry, expression, texture and unrelated regions. Do not repeat global strength changes or full face generation. The latest v4.1 appearance is not accepted. Local audit records limitations before further rendering. Separate reference photograph identity is NEEDS VERIFICATION if different from the stored generated guides. No production change is approved by this review. [Evidence](../docs/experiments/makeup-realism-audit-20261102.md).


## Implement source correction without promoting failed looks, 2026-11-02

**CONFIRMED:** User requests implementation and testing after tracing the actual Makeup path, preserving the original person and working system. No major architecture replacement is approved by that request. Bounded lip correction is implemented offline. The new combined cheek/eye proof remains rejected; passing source preservation checks do not justify release. Lip only is a component test, not the user's desired finished look. **PROPOSED:** artist/salon approved explicit cosmetic layers to replace ambiguous extraction from generated faces, with one concrete full look validated before integration. No such approved layer set is claimed. [Evidence](../docs/experiments/makeup-source-surface-20261102.md).


## Preserve the preferred lip correction, 2026-11-03

**CONFIRMED:** User says the latest result is much better and clarifies that this means Lip correction ONLY. They authorize only necessary refinements after review, explicitly permitting no change if further work is not justified by the current method. The preferred local v4.1 result remains unchanged. The feedback does not approve full Makeup, the rejected combined proof, automatic catalog expansion or deployment. Safe future edge or shade work needs evidence beyond simply widening a mask or deepening a palette. [Review](../docs/experiments/makeup-retained-review-20261103.md).


## Source fitted artist Makeup direction, 2026-11-04

**CONFIRMED:** In response to the explicit source choice question, Supervisor selects artist/salon authored cosmetic layers fitted to the original portrait. This resolves the 2 November PROPOSED direction for isolated offline preparation. Preserve the preferred lip component, all ten serving plus three held styles, the existing FLUX/LoRA foundation and application contracts. Target preparation and future adapter behavior remain separate validation responsibilities. No artist asset approval, full look acceptance, corrective training or production integration follows from choosing this direction. Mandatory corrective quality admission implements the stated requirement that defective targets cannot automatically become training data. [Spec](../docs/specs/0016-makeup-source-layer-quality.md), [implementation and limits](../docs/experiments/makeup-architecture-review-20261104.md).


## Artist prerequisite removed, automatic Makeup work resumed, 2026-11-04

**CONFIRMED:** Supervisor has no available makeup artist and explicitly requests the original engineering task. **DEPRECATED:** external artist assets as a mandatory critical path from the preceding answer/spec0016. Retain useful source application and target quality gates; do not fabricate artist acceptance or ask the user to implement masks. Engineering implements a bounded automatic local feature/material correction under the original technical freedom. **PROPOSED:** adoption of this isolated pretrained CPU feature provider beyond local review; no production model replacement or training target approval is inferred. The confirmed FLUX/LoRA foundation and existing application contracts remain. Actual52casecomparison and documented quality gaps precede any target finalization, distinct corrective adapter training or integration. [Spec0017](../docs/specs/0017-makeup-automatic-local-features.md), [evidence](../docs/experiments/makeup-automatic-correction-20261104.md).

## Guided inference fails visual gate, 2026-11-05

**CONFIRMED engineering rejection / DEPRECATED promotion of this fixed guided inference attempt:** Returned two case real MAKEUP-001 test matches the prepared model, environment, inputs and settings but produces severe whitening on054109and plastic reconstructed faces on both. Do not extend to all13styles, admit targets or integrate this approach. Existing full Makeup requirement remains. **PROPOSED next correction:** reviewed complete photographic targets and a separately trained/evaluated corrective adapter on the existing FLUX/LoRA foundation; no training, target set or new production architecture is approved by the failed run. Existing Hair/Nails release, source data/checkpoints and positive teacher direction retained. [Evidence](../docs/experiments/makeup-guided-gpu-review-20261105.md).

## Complete Makeup direction and bounded GPU check, 2026-11-05

**CONFIRMED:** Supervisor accepts prepared external editor035149Bold Evening fourth panel as the complete makeup direction and can start the existing GPU notebook. This accepts direction only, not targets, model quality or release. Both new local whole look reviews were rejected as too weak; their new material/gradient methods are DEPRECATED for promotion. Preserve the existing lip component, all13styles, original datasets/models, and18Hair/8Nails prepared release.

**PROPOSED production use, authorized bounded diagnosis:** reuse existing MAKEUP-001 with the original and a different training identity cosmetic guide as separate conditioning images. The pinned pipeline supports this input; visual behavior is unverified. Two private raw output calls precede any wider run or serving change. External editor guides are truthfully synthetic, not our model output, artist assets or accepted training pairs. Individual data admission, corrective training, Base comparison and production integration remain separate. [Spec0018](../docs/specs/0018-makeup-complexion-release.md), [evidence](../docs/experiments/makeup-complete-direction-20261105.md).

## Proceed with bounded material defects, 2026-11-05

**CONFIRMED:** Supervisor says proceed after identification of remaining lip, lash, metallic and finish gaps. Extend the same automatic source application and reuse cached neural fields; no artist prerequisite or speculative Kaggle spend. Original positive lip helper/default baseline remain reproducible. Existing user photo supplies foreground material detail for local review; its unknown author/license is retained rather than treated as a training permission. **PROPOSED:** any use of new source materials beyond isolated review. The52casecomparison improves lip hue/coverage and visible detail but leaves documented lash/Manga/metal/finish gaps. No human catalog acceptance, target admission, corrective training or production approval follows from passing119checks. Existing FLUX/LoRA model architecture and Hair/Nails contracts remain. [Spec0017](../docs/specs/0017-makeup-automatic-local-features.md), [evidence](../docs/experiments/makeup-material-refinement-20261105.md).


## Corrected Makeup supervision and target appearance approvals, 2026-11-05

**CONFIRMED:** User authorizes developing the fix and accepts13representativepreparedtargetappearances,10fromhashboundexportand3specificrevisionsviachat. Keep those image/caption bytes and the complete13stylecatalog. Corrective data uses explicit style supervision rather than the historical one-caption60pair set. Author new photographic synthetic targets fitted to original identity/scene; no artist prerequisite and no inference-only claimed training solution.

**CONFIRMED engineering data correction under existing scope:** Add audited originals003025and027921to training for broader complexion coverage, without moving either existing validation identity. The planned dataset remains52train/26validationpairs, now12train/2validationidentities. v4sourcebrowrelativecontrastreplaces the failed absolute RGB stamp for additional targets;13approvedimages remain unchanged. Existing FLUX/LoRA foundation retained, fresh corrective candidate rather than continuation/overwrite of old weights. Production adoption remains PROPOSED pending a complete admitted dataset, actual new model evaluation and project lead review.

## Corrective full candidate review boundary, 5 November 2026

**CONFIRMED:** Preserve all13explicitappearanceapprovals and their exact targets/captions. Added65identity/styleappearancesrequire actual review, not representative approval propagation. Existing individual quality policy remains mandatory before DATA finalization/packaging/training. 78preparedpairsare candidates, not an accepted dataset.

**DEPRECATED for new candidate preparation:** v4 scalar brow density after full batch exposes flat/gray plates. **CONFIRMED engineering correction within the existing source-fit scope:** v5 retains original RGB brow gradients and fits their boundary colour to foundation using existing OpenCV, without a new model/provider/dependency. The13approvedv3targetsremain untouched. Neither a cap sweep nor the RGB ratio probe is adopted. Production integration remains PROPOSED pending admitted DATA, actual corrected adapter evaluation and Project Lead review.

## Full corrective DATA approval, 6 November 2026

**CONFIRMED:** Supervisor explicitly confirms reviewing all 78 candidates and accepting them on all eight criteria after the uploaded export recorded only six acceptances. Preserve both the original return and exact chat clarification, bound to existing images/captions. All 78 unchanged targets are admitted; do not request their appearance approval again. Finalize a separate DATA copy and proceed to the existing authorized fresh Base corrective adapter run. This is training DATA acceptance, not model or production approval. The same pinned FLUX/LoRA foundation and bounded 250 step configuration remain. Production adoption is PROPOSED until actual new adapter quality and application validation pass.


## Corrective RAW model acceptance, 6 November 2026

CONFIRMED: Supervisor returns `makeup-corrective-model-review.json`, SHA256 `7db6666beb345275462d3358bac1e3db8f431f441caeb2db6f4235c0b573f3df`, and says the corrective RAW real generations look great. All 26 bound cases accept application validation across 13 styles. Its production approval flag remains false.

Advance the existing controlled application milestone with the new checkpoint and exact successful captions. No further target audit or training by default. Candidate retains 18 Hair/8 Nails and exposes all 13 Makeup styles only in the isolated test. Preserve old artifacts/contracts; do not register a production endpoint in this validation notebook. Fresh application/website evidence and project lead production review remain open. [Evidence](../docs/experiments/makeup-corrective-model-results-20261106.md).


## Application acceptance and proposed production rollout, 6 November 2026

VERIFIED: every one of 13 real application Makeup outputs is the exact PNG already accepted by the Supervisor in the model review. Do not request another visual audit of identical pixels. All 16 feature requests and active tensor checks pass; fresh identity/website acceptance remains separate.

PROPOSED production action: apply and publish the prepared `styles-20261106-01` source/metadata and matching immutable CPU/notebook candidate, then deploy the matched Render/Kaggle release. Retain the same tested model/generation code, 18 Hair/13 Makeup/8 Nails and all three truthful older fallbacks. Original task explicitly reserves production integration for project lead review. Candidate is reviewable and locally checked; no production approval, source application, publication or cloud deployment inferred from receiving this ZIP. [Review](../docs/guides/makeup-corrective001-release.md).


## Production rollout authorized and web release deployed, 6 November 2026

CONFIRMED: “Can we now deploy it?” authorizes applying/publishing the presented styles-20261106-01 release and matched Render/Kaggle rollout. No further production permission question is needed within that exact scope. Existing source/runtime verification remains required. The final serving notebook's missing Makeup startup membership was corrected without changing generation. VERIFIED publication578330d and actual Render Live deployment; Kaggle authentication/connection remains open. Preserve all previous inputs and compatible fallback catalogs. [Evidence](../docs/experiments/makeup-corrective-deployment-20261106.md).


## User manual browser control, 6 November 2026

CONFIRMED: user asks “CAN I JUST DO IT MYSELF”; stop browser control and hand over final startup steps. Do not resume browser actions merely because the user asks a subsequent packaging question. Existing deployment authorization persists. A complete local client handoff may be prepared; no client message/file transmission is authorized by saying they will send it themselves. Current question establishes intended client delivery by the user. [Evidence](../docs/experiments/makeup-corrective-client-handoff-20261106.md).

## Complete public source handoff, 7 November 2026

CONFIRMED: Supervisor requests pushing all project work for client use and modification, then specifies accessible to all. Publish the complete source and development evidence, retaining previous history and private local originals. The existing repository is already public. Include the reviewed deployment history on default `main` and align the serving source branch through normal fast forwards. Keep credentials, image datasets and model packages outside public Git. Direct pushes require a collaborator account; public users may fork and contribute through pull requests. This does not authorize sending client messages, disclosing secrets, transferring provider ownership or claiming unresolved Kaggle startup has passed. [Record](../docs/experiments/client-source-publication-20261107.md).

## Alternative GPU provider research, 8 November 2026

PROPOSED research recommendation at that point: prefer one Runpod Pod for the first move away from Kaggle, retaining the Render website, existing shared foundation/adapters, serialized generation and API contracts. Select allocated RAM sufficient for the current 30 GiB requirement, persistent cache and a pinned runtime. Lightning Studios, Vast instances and Modal are alternatives with different setup, billing and lifecycle costs. Public pricing research alone does not approve a provider purchase, deployment cutover or serverless redesign. [Research](../docs/research/gpu-hosting-alternatives-20261108.md). The following preparation authorization is the later decision.

## Runpod server preparation with Kaggle backup, 8 November 2026

CONFIRMED: Supervisor asks to prepare the server for Runpod deployment while retaining Kaggle as backup, then chooses continued local verification. Prepare a separate candidate using existing model/application code and private inputs. Preserve Kaggle sources, guards and artifacts. The first candidate uses RTX 3090 with a separately declared profile and the existing authenticated tunnel/registration contract, without a Render/database/UI change. Do not infer paid resource purchase, completed Linux build, hardware quality acceptance, automatic provider failover or live cutover from local preparation. [Spec](../docs/specs/0019-runpod-serving.md), [evidence](../docs/experiments/runpod-preparation-20261108.md).
