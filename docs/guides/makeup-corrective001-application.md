# Validate the accepted Makeup model in the application

The 250 step corrective model is trained. Your returned review accepts all 26 real model images across all 13 styles. No more target authoring, target audit or training is needed for this milestone.

The next notebook tests the same model through the existing application API and shared Hair/Makeup/Nails GPU worker. It does not register with or change the live website.

## Files

All new files are in `I:/HAIR/artifacts/makeup-corrective-supervision-20261105/application-candidate-01/`.

1. Import `makeup_corrective001_application.ipynb` into a separate private copy of your previously working pinned Kaggle notebook.
2. Attach the new `makeup_corrective001_application_candidate_20261106.bin` as an input.
3. Also attach the existing unchanged `capstone_train002_20260928_v1.bin` used by the combined serving notebook. The training input ZIP and training results ZIP are not the inputs for this application notebook.

Use one copy of each input filename. Preserve the earlier notebooks and datasets. Select the same reviewed T4 environment and enable Internet plus the existing `AI_BACKEND_API_KEY`, `AI_REMOTE_API_KEY` and `GEMINI_API_KEY` secrets. No new secret or manual Render setting is needed. Keep values private.

## Run

Run the three code cells once, in order. Cell 1 verifies/extracts both inputs. Cell 2 starts the existing shared worker and authenticated local application API. It prints `CONTROLLED APPLICATION READY`. Cell 3 performs the bounded application checks and returns `makeup_corrective001_application_results.zip` in Kaggle working output.

Cell 3 makes 13 Makeup application generations, two expanded Hair application generations and one Nails GPU crop request. Budget roughly 20 minutes for those generation checks, plus cold dependency/model startup. This is an estimate from the returned Makeup timings, not a verified application runtime measurement. The actual outputs and timings will be saved.

Return that ZIP. Its gallery compares Original | Accepted model RAW | Application RAW. The run verifies exact model/prompt metadata, active adapter tensors and restoration across features. It preserves partial results on failure. If an admitted generation has uncertain completion, do not resend it or repeatedly rerun the cell. Keep the exact printed stage and return the preserved results.

## What remains

This candidate contains 18 Hair, 13 Makeup and 8 Nails API entries. The three expanded Makeup styles are available only in this isolated test package. The website release and its current session remain unchanged.

The Nails crop tests the shared GPU adapter, not full hand fitting. Fresh portrait upload, website and consultation generation, save/book, mobile acceptance and matching production release remain separate checks. Once the application return is verified, the next step is the production candidate and rollout review, not another training run by default.

Exact package hashes and local verification are in `package.json`, `handoff.json`, `cpu-preflight.json` and `preservation.json` beside the notebook. Full results and limits are in [the model report](../experiments/makeup-corrective-model-results-20261106.md).
