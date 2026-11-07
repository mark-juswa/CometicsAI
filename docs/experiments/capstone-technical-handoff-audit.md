# Capstone technical handoff inspection, October 4, 2026

**Progress:** DONE for documentation inspection and authoring.  
**Evidence:** VERIFIED source/artifact inspection; historical runtime evidence cited with its original boundaries.  
**Source:** `codex/mobile-02`, commit `1ab147e055a00f7694a77bda96f938c3166c2888`.  
**Deliverable:** [Client technical handoff](../guides/capstone-technical-handoff.md).

This task created documentation. It did not train a model, generate an AI image, start services, control a phone, change configuration, mutate the database, or close outstanding runtime acceptance gates. The preexisting untracked `context/designs/` directory was left untouched.

## Inspected evidence

| Area | Inspected sources |
| --- | --- |
| Project authority | Root AGENTS; current state; project, architecture, AI/ML, data, evaluation, engineering and decisions context; roadmap; unified folder, Consultation and mobile specifications |
| Data and training | DATA-001, DATA-002, DATA-M001 and DATA-N001 records; training runners; adapter metadata; TRAIN-001/002, Makeup and localized Nails evaluations; Nails verification JSON; recovered DATA-002 archive report |
| Current web boundary | BeautyCore package, AI catch-all route, adapter core, signed handles, auth utilities, database schema/driver, older analyze/generate/provider paths and Client Advisor redirect |
| Current image processing | FastAPI dispatch/validation, Hair and Makeup remote clients, model contracts, Nails hybrid/geometry/segmentation/localized/render logic and shared destination selection |
| GPU runtime | Unified server, Gate 2 switch owner, original generation methods, pinned runtime requirements and Gate 3 live-review JSON |
| Mobile | Package/app configuration, API client, File multipart upload, temporary stores, Custom Save/Share implementation, Consultation result Select and dated native evidence |
| Startup | Root START and START_MOBILE, BeautyCore launcher, discovery/package mapping, ntfy signed metadata and Cloudflare tunnel constraints |

External primary references were checked for the model's high-level explanation, pipeline component list, training toolkit and dataset origins. These references do not prove project training or runtime acceptance. Project claims rely on the repository and preserved experiment records.

## Fresh local artifact observations

All four adapter byte sizes are 46,223,600. SHA-256 observations matched the production contracts or corresponding registry metadata:

| Artifact inspected | Observed SHA-256 |
| --- | --- |
| `artifacts/train001_adapter_bundle/adapter.safetensors` | `7e3991f8a4e502573d3e82e9ac34c89fdf3f0b66fb337abb026a5b4c9ad080ff` |
| `artifacts/train002_adapter_bundle/adapter.safetensors` | `59d527217a68139bc2aaa4eedbfcd2d5789ef115f8ecb924410eea24a952939b` |
| `.tmp/makeup001/runtime_verification/adapter/adapter.safetensors` | `f6f0419e4259a75102f08a450222ad806e3aec1c2ae50ff89f875139084ae510` |
| `adapter/nails001_local_v1.safetensors` inside the existing private Nails runtime package | `5bff16c67e0014c78a6d938813347685f914f8a608d76407b10f5b54b7a0eb1f` |

The Nails runtime package itself was present at 42,214,993 bytes and matched `adf324b0e2bcf6f23f34641c6448b8874898e4b910750c7cc8fe9c002f072699`. Local MediaPipe and YOLO checkpoints were present; their hashes matched `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1` and `99b7d1c6ceb4bde32d80fe7ae8c8eb809c27d99b55cf9db54b6692afe68f4070`, respectively. Presence is not a new detector-quality test.

The retained MAKEUP-001 `training_summary.json` reported success, exit 0, step 250, no stop reason, final save after the last step, 8,623 seconds including load, 13,531 MiB observed whole-GPU peak, and 498 finite loss observations. Its retained configuration matches the described paired-reference BF16/LoRA setup. These are re-read historical run records, not a new training run.

Only explicitly selected nonsensitive configuration fields were exposed during inspection. Local file settings select Hair `remote_flux`, Makeup `remote_makeup`, Nails `hybrid` at 8 inference steps, Gemini consultation and the expanded Hair registry. BeautyCore's old preview path selects `stub`. Launcher source can override the file-selected Hair registry according to signed package identity. Therefore this observation does not establish the active runtime catalog.

Three read-only local catalog requests to port 8000, one per feature with a three-second timeout, returned connection errors (`URLError`). No response body or current worker status was available. No service restart or GPU request followed. Current availability remains **NEEDS VERIFICATION**; dated live tests are presented as dated tests.

## Findings that shape the client explanation

1. Custom AI means project-trained generative LoRA adapters on external FLUX, with direct pixel contribution. It does not mean a new foundation trained from scratch.
2. DATA-M001 uses the reviewed external bare-to-makeup pairs. Earlier failed synthetic/preservation/inpainting experiments are not its final training data. Its numeric variants are not semantic style classes.
3. Nails step 50 failed five-style quality. Current code intentionally routes Red/Black to its adapter and the other three styles to the renderer. The common final compositor preserves pixels outside the selected mask, not necessarily outside the true anatomical nail.
4. Shared GPU serving is implemented and historically verified at capstone scale, with one loaded foundation and serialized adapter switching. Earlier proposed-only statements are superseded.
5. BeautyCore is the current root-launched app, with private FastAPI behind its authenticated AI bridge. The old `frontend/` and older provider APIs remain distinct paths.
6. The inspected AI bridge does not write current generated results into BeautyCore's older AI-generations table. Consultation is bounded temporary process memory. Select is not booking/payment.
7. Gemini consultation receives text and catalog metadata, not the uploaded photo. Its primary recommendations are validated before existing generators are called.
8. Current mobile generation uses BeautyCore cookies and SDK 57 File multipart. Hair native acceptance has logs plus Supervisor manual confirmations. Standalone Android Makeup visual and Nails live acceptance stay deferred.
9. A current local connection failure prevents claiming a fresh live rehearsal in this task.

## Documentation drift and specification reconciliation

**DOCUMENTATION DRIFT:** `context/project.md` still states that real data/LoRA are not started. Early `context/ai-ml.md` and `context/data.md` passages retain pre-training states, and some experiment headings/README/spec language retains earlier pending gates. Later artifacts and dated results establish real training, unified serving and representative mobile Hair completion. Those older texts were not wholesale rewritten in this task.

No unresolved major architecture conflict was found in the inspected current paths. The handoff follows the confirmed unified BeautyCore/private FastAPI/Kaggle boundary and the explicit mobile deferrals. It does not reinterpret the original standalone mock mobile specifications as the current authenticated architecture.

The unified-folder spec's full client portability and deployment acceptance, the original repeatable deployment rehearsal, all-style quality, durable jobs/history and remaining native gates are not declared complete. The roadmap gains a documentation deliverable only. No new architecture decision is made.

## Document validation

Validation checks and their results are recorded in [the companion JSON](capstone-technical-handoff-validation.json). They cover local Markdown link targets and heading anchors, balanced code fences, the three Mermaid blocks' structural consistency, required topic coverage, adapter/configuration assertions, and a scan for configured private values and temporary tunnel URLs. Diagram structure checking is not a rendered Mermaid acceptance test. Historical application suites were not rerun for a prose-only change.
