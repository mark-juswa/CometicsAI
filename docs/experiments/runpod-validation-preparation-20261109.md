# Runpod real generation validation preparation

DONE reusable probe adaptation and local tests. NEEDS VERIFICATION actual Runpod generations and human visual review. No GPU requests or website registration performed by Codex.

## Startup evidence

The user reports `READY_FOR_RUNPOD_VALIDATION Release: styles-20261106-01`, run `/workspace/beautycore/runs/94a17b8710e34e48a7cd9a8596d11eb4`, and 18 Hair, 13 Makeup, 8 Nails. This establishes operator observed successful guarded startup, not real image quality. The prior user Terminal hardware check confirmed an RTX A6000, 47.4 GiB VRAM, 46.57 GiB allocated RAM, Torch2.10.0+cu128, compiled CUDA12.8 and tiny CUDA initialization. Model load and readiness are now reported; actual application outputs remain pending.

## Small correction

The existing `makeup_corrective_application_probe.py` uses Kaggle Secrets, a Kaggle download path and IPython display. Its fixed cases and metadata checks already cover the accepted application release. The actual immutable CPU archive contains both reviewed development portraits, all13 accepted RAW comparison images, the original probe and corrective model bindings.

Extend the same `run` function with optional secret client, archive directory, display and execution provider inputs. Defaults retain Kaggle behavior and filename. Add a standalone `runpod` CLI reading private environment secrets, checking latest run belongs to the workspace, requiring validation-only readiness and the exact release, and refusing a configured website URL. A failed/uncertain run returns a nonzero exit. It never retries generation, overwrites previous case folders, changes model files or weakens provenance checks. The existing private archives and serving image remain unchanged. No new Docker image is required.

## Cases and review

Use the existing16 cases once: all13 Makeup styles across two known identities, two expanded Hair styles, and the existing Nails prepared-crop worker request. Verify one foundation, active tensor equality and response/worker adapter agreement. Preserve original/accepted RAW/Runpod output comparisons and exact model/caption/settings checks. Hardware differences may change output pixels; byte inequality alone is not a visual verdict. Review the actual images.

The Nails crop checks adapter switching, not full-hand localization/blending. Fresh identities, full-hand Nails, website/Consultation, save/booking, mobile and restart acceptance remain separate open gates. Do not call this production ready from readiness or training completion alone.

## Local verification

55 checks pass with one historical test deselected. New tests cover environment-backed execution, persistent result path, refusal of registered/wrong-release/outside-workspace/missing-secret sessions, nonzero uncertain result without replay, complete synthetic16 case archiving and result preservation after an uncertain admitted job. Existing model response drift guards and all31 Runpod preparation checks pass. Synthetic images/HTTP responses are unit fixtures, not model quality evidence.

The unchanged historical `test_candidate_uses_exact_thirteen_accepted_captions_without_changing_legacy_contract` fails because the historical candidate packager searches for legacy `ADAPTER_ID = MAKEUP-001` while current approved source is already corrective. This path is independent of the probe adaptation and is not used for current runtime validation. An initial test run also lacked backend on PYTHONPATH. Corrected test command:

```powershell
$env:PYTHONPATH = 'I:\HAIR\backend;I:\HAIR'
python -m pytest backend/tests/test_runpod_application_probe.py backend/tests/test_runpod_preparation.py backend/tests/test_makeup_corrective_application.py -q -k 'not candidate_uses_exact_thirteen_accepted_captions_without_changing_legacy_contract'
```

## Operator step

Keep the server terminal running. Upload the updated standalone `scripts/makeup_corrective_application_probe.py` into Jupyter at `/workspace/makeup_corrective_application_probe.py`. Use a second Terminal:

```bash
python /workspace/makeup_corrective_application_probe.py runpod
```

Run once. Output ZIP is `/workspace/beautycore/validation/runpod_application_results.zip`. Download it privately and review/share it with the project lead. On failure or uncertainty, preserve the ZIP and admitted job ID; do not replay the command. A successful technical status still reads `TECHNICAL_PASS_VISUAL_REVIEW_PENDING`. Website URL remains absent until results are reviewed and accepted.
