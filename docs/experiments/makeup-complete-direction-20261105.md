# Complete Makeup direction and real model handoff

5 November 2026. **Full Makeup IN PROGRESS. Local package verification VERIFIED. Actual guided MAKEUP-001 output NEEDS VERIFICATION. Production integration NOT STARTED.**

## Finding and user review

The earlier52casegallery improved lipstick but did not deliver the requested complete makeup. The twelve case `whole-face-review` and the four case `visual-review-02` were both explicitly rejected as too weak or unchanged. Adding more local complexion coverage did not establish success. Stronger signed surface and gradient alternatives produced orange or pale patches, hard eye boundaries or an artificial surface during engineering inspection. They remain rejected, with sources and outputs preserved in `artifacts/makeup-complexion-release-20261105/`. No failed variant was integrated.

Supervisor then reviewed the fourth panel of [035149-comparison-v2.png](../../artifacts/makeup-complexion-release-20261105/teacher-proof/035149-comparison-v2.png) and answered **“Yes, this is the complete makeup direction.”** This is the first positive complete look direction in this cycle. It is an external editor proof fitted to the original portrait, not a MAKEUP-001 result. The user also confirmed they can start the existing GPU notebook. Neither answer establishes GPU generation, all style acceptance, data admission or production readiness.

## Current architecture

| Responsibility | Actual location and behavior |
|---|---|
| Training sources and historical pairs | FFHQ-Makeup paired selection, provenance manifests and DATA-M001 finalization/package scripts; historical training used50train/10validation pairs on10train/2validation identities |
| Target admission | `scripts/makeup_target_quality.py` and corrective review infrastructure require individual source/target/caption/hash bound review; all60historical targets remain rejected for unchanged corrective reuse |
| Active style intent | Ten fixed inference presets in `data/makeup/DATA-M001-paired/inference_presets.json`, hash checked by `backend/app/makeup_contract.py` |
| Expanded Makeup catalog | Three held candidates in `backend/app/style_release.json` |
| Actual generation | `scripts/makeup_inference_server.py:MakeupRuntime.generate`, used by the unified worker; one source portrait plus a text preset into the pinned FLUX.2 Klein Base4B with trained MAKEUP-001,20steps,guidance4,seed1977 |
| Returned result | Whole generated face, without a source pixel identity or complexion lock |
| Prior corrective proofs | Offline `makeup_source_layers.py`, `makeup_materials.py` and evaluator; not imported by serving |
| Application and release | Existing BeautyCore/Render, central FastAPI facade and private shared Kaggle worker; existing Makeup API remains unchanged |

## Root cause assessment

**Demonstrated source defect:** existing makeup targets can already lighten skin, smooth texture and reconstruct features. Their full appearance is unsuitable as unquestioned cosmetic ground truth. The historical rejection policy is retained. This does not prove how much of a particular learned output comes from training bias.

**Demonstrated model behavior:** global Base and adapter generation have changed facial appearance despite preservation text. The serving implementation returns that entire output. Prompt wording provides no exact feature or skin guarantee. Whether the trained adapter specifically amplifies each defect remains a causal hypothesis, not a proven sole cause.

**Demonstrated application defect:** the local source compositor preserved the portrait but could not represent a sufficiently complete, naturally blended base and coordinated cosmetic finish. Its positive lip result is a component, not whole makeup. The subsequent two rejected full look reviews show that adding controlled source shade coverage was insufficient. Technical mask equality and distinct image hashes did not establish appearance success.

**New testable hypothesis:** the existing model may respond better to an explicit complete cosmetic image guide separated from the original identity reference than to text alone or a pale whole face transfer. The exact installed Diffusers commit accepts multiple reference images. This API capability is verified from [the primary source](https://github.com/huggingface/diffusers/blob/c943837899b16cbae2f619b8dd4f7bb6f07dd81a/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py). Cosmetics quality, source anchoring and memory with a second guide are unverified until the GPU test returns.

## Complete style inventory

| Status | Styles |
|---|---|
| Existing ten serving presets | Natural Makeup; No-Makeup Makeup; Soft Glam; Smoky Glam; Dewy Peach; Rosy Pink; Bronze / Golden Glam; Matte Nude; Classic Red Lip; Bold Evening Glam |
| Three expanded, currently held | Cloud-Skin Makeup with Blurred Berry Lips; Manga-Lash Makeup; Icy Silver Eye Makeup |

All13remain in scope. No held Makeup style is silently enabled. The next bounded proof covers medium and bold looks, not the catalog.

## Small correction and implementation

Keep the current foundation and our trained MAKEUP-001 adapter. Test two reference inputs in a private diagnostic. The original portrait is the identity, skin, anatomy, expression, lighting and scene reference. A separate training identity supplies only a complete cosmetic guide. The effective prompt explicitly assigns those roles and requests foundation shade matched to the original. Raw model output is retained so an identity or complexion failure stays visible.

| File | Responsibility |
|---|---|
| `scripts/prepare_makeup_teacher.py` | Reusable offline fitting of a labeled external teacher image to its original portrait, using existing mesh registration, parser and feature protection; no automatic training admission |
| `scripts/makeup_reference_diagnostic.py` | Exactly two actual model calls; original environment/model/adapter/tensor/scaling checks, raw PNGs, truthful prompts/provenance and comparisons, partial report on failure |
| `scripts/makeup_quality_bootstrap.py` | Small allowlisted runner parameter; old default diagnostic remains the default |
| `scripts/makeup_reference_bootstrap.py` | Selects that runner through the existing pinned bootstrap rather than duplicating model infrastructure |
| `scripts/package_makeup_reference_diagnostic.py` | Builds a private self contained notebook using the existing safe GPU archive extraction and payload hashes |
| `data/makeup/MAKEUP-GUIDED-001/plan.json` | Exact two case manifest with source/guide identities, split roles, credits, hashes and frozen inference settings; not a finalized training dataset |
| `backend/tests/test_makeup_reference_diagnostic.py` | Mocked two input call order, raw output, one foundation, full adapter influence and partial failure/no retry behavior |

Failed new local material branches were archived under `rejected-implementation/`, and the three pre attempt helper snapshots restored. The unused finisher using the rejected material method was archived out of scripts. The added failed Poisson helper was removed while retaining the historical blend function. Earlier datasets, checkpoints, experiment outputs and positive lip implementation remain intact.

## Validation and comparisons

| Evidence | Result and limit |
|---|---|
| Approved035149Bold Evening prepared teacher | Complete makeup direction accepted by Supervisor. Generalized preparation reproduces the exact PNG SHA588e15c1ada01230865b794b181e250dd8a4c7d2e4ad9063cf3f0f022743dc88. Original eye cores, brows, mouth/teeth, measured nostril core and nonface scene are exact. This is not a full geometry or skin realism score. |
| Prepared006553Soft Glam guide | Visible complete cosmetics on a different training identity. Source protected checks pass; human approval pending. Median skin Lab change[0,+5.21875,+6.625] includes intentional cheek makeup and is not an undertone accuracy score. |
| Exploratory054109Soft Glam raw teacher | Preserved as external editor output; not used as this portrait's guide, not admitted or accepted |
| Private GPU case1 | Original054109deep complexion, Soft Glam guide006553. **No returned GPU result yet.** |
| Private GPU case2 | Original056266fair complexion, Bold Evening guide035149. **No returned GPU result yet.** |
| Local package | Original GPU bundle SHA/internal manifests, six embedded source files, six images and code compilation pass. Invalid guide split/identity/path and changed guide bytes are refused. Existing local API busy guard was exercised and refused; the API was left running. |
| Focused regression |139tests passed in33.14seconds, including two new mocked orchestration tests. No GPU quality inference follows from mocked tests. |
| Preservation |92of94earlierfrozenfiles unchanged. The same two deliberate prior evaluator/application changes remain. All52Nov4catalogPNGs and all8capturedserving/releasecontrols are unchanged. |

The GPU notebook builds `Original | Different-person cosmetic guide | Previous rejected CPU result | Actual MAKEUP-001 raw` comparisons. The Previous panel is explicitly not a matched model baseline. A stronger causal Base versus adapter or old versus new conditioning comparison remains a separate evaluation requirement after this initial viability gate; do not present the external teacher as that evidence.

Notebook: [complete_makeup_gpu_check.ipynb](../../artifacts/makeup-complexion-release-20261105/gpu-check/complete_makeup_gpu_check.ipynb). Private copy of the existing working pinned Kaggle image, original GPU bundle input, GPU and Internet enabled, two code cells once. No old training/service cells. Preserve and return `beautycore-makeup-reference-results.zip`, including partial failure. No API server, tunnel, Render change, training or extra sweep occurs in this check.

Full local receipts: [validation.json](../../artifacts/makeup-complexion-release-20261105/validation.json), [package preflight](../../artifacts/makeup-complexion-release-20261105/gpu-check/preflight.json), [synthetic provenance and prompt records](../../artifacts/makeup-complexion-release-20261105/teacher-proof/generation-provenance.json). The first teacher prompt was not persisted exactly before context compaction; its record is explicitly a summary. This gap is disclosed and does not become truthful complete training provenance by assumption.

## Coverage, preservation and next milestone

Current evidence establishes an approved complete look direction on one development portrait and a verified private test package. It does not establish corrected MAKEUP-001 behavior on any portrait, full13style quality, runtime memory/latency, application acceptance or production readiness. Warm/cool, subtle/strong eye and lip looks, allcomplexions and arbitrary upload fitting remain unverified for the new guided model path.

Hair and Nails source, UI, contracts and release are unaffected. The latest prepared combined release is `styles-20261031-02`,18Hair/10Makeup/8Nails. Its guide still requires matching Render deployment and fresh Kaggle/website rehearsal; existing historical acceptance is not a fresh live check. No push or cloud deployment occurred here.

**Next milestone:** return and inspect the two real model outputs. If either fails complete cosmetics, identity, complexion or texture, stop promotion. If both are credible, proceed with all13style guides and broader actual model comparisons, then unchanged API/application validation and project lead production review. Dataset finalization has zero newly accepted pairs and remains blocked by individual target admission. Corrective training is NOT STARTED; existing MAKEUP-001 was already trained250steps. No new corrective run, Base comparison or production integration is claimed. These remain separate milestones, without an artist prerequisite or invented today delivery guarantee.
